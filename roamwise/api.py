from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

from roamwise.common import log


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(min_length=3, max_length=500)
    city: Literal["Boston", "Cambridge", "Somerville"] | None = None
    category: Literal["food", "culture", "outdoors", "lodging"] | None = None
    top_k: int = Field(default=5, ge=1, le=10)
    method: Literal["semantic", "baseline"] = "semantic"

    @field_validator("query")
    @classmethod
    def strip_query(cls, value):
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Enter at least three non-space characters")
        return value


def create_app(engine=None, language_model=None):
    from roamwise.llm import JSONModel, ModelUnavailable
    from roamwise.planner import Planner, TripRequest, ItineraryRequest, GroundingError
    from pydantic import ValidationError

    @asynccontextmanager
    async def lifespan(application):
        if engine is None:
            from roamwise.retrieval import Retriever

            application.state.engine = Retriever()
        yield

    application = FastAPI(title="RoamWise", version="0.2.0", lifespan=lifespan)
    application.state.engine = engine
    application.state.model_factory = (lambda: language_model) if language_model else JSONModel

    @application.get("/api/health")
    def health():
        if application.state.engine is None:
            raise HTTPException(503, "Index is not ready")
        return {
            "status": "ok",
            "dataset_id": application.state.engine.dataset["dataset_id"],
        }

    @application.get("/api/status")
    def status():
        retriever = application.state.engine
        if retriever is None:
            raise HTTPException(503, "Index is not ready")
        import os
        return {"dataset": retriever.dataset, "index": retriever.index,
                "generation": application.state.model_factory().describe(),
                "google_places_configured": bool(os.getenv("GOOGLE_PLACES_API_KEY") or os.getenv("GOOGLE_PLACES_AUTH") == "adc")}

    def run_planner(action, request):
        retriever = application.state.engine
        if retriever is None:
            raise HTTPException(503, "Index is not ready")
        model = application.state.model_factory()
        try:
            result = getattr(Planner(retriever, model), action)(request)
        except GroundingError as exc:
            raise HTTPException(422, str(exc)) from exc
        except (ModelUnavailable, ValidationError) as exc:
            log("generation_failed", error_type=type(exc).__name__)
            raise HTTPException(503, "The model could not produce a valid response. Please retry; no draft was substituted.") from exc
        log("rag_complete", action=action, dataset_id=retriever.dataset["dataset_id"],
            prompt_version=result.get("prompt_version"), elapsed_ms=result.get("elapsed_ms"),
            model=model.describe(), calls=getattr(model, "calls", []))
        return result

    @application.post("/api/recommend")
    def recommend(request: TripRequest):
        return run_planner("recommend", request)

    @application.post("/api/itinerary")
    def itinerary(request: ItineraryRequest):
        return run_planner("itinerary", request)

    @application.get("/api/places/{place_id}/live")
    def live_details(place_id: str):
        from roamwise.data_agent import GooglePlaces, SourceUnavailable
        retriever = application.state.engine
        place = retriever.places.get(place_id) if retriever else None
        if not place:
            raise HTTPException(404, "Place not found")
        try:
            return GooglePlaces().lookup(place["name"], place["city"])
        except SourceUnavailable as exc:
            raise HTTPException(503, str(exc)) from exc

    @application.post("/api/search")
    def search(request: SearchRequest):
        retriever = application.state.engine
        if retriever is None:
            raise HTTPException(503, "Index is not ready")
        response = retriever.search(**request.model_dump())
        log(
            "search",
            method=request.method,
            results=len(response["results"]),
            elapsed_ms=response["elapsed_ms"],
            dataset_id=response["dataset_id"],
        )
        return response

    @application.get("/api/places/{place_id}")
    def detail(place_id: str):
        retriever = application.state.engine
        if retriever is None:
            raise HTTPException(503, "Index is not ready")
        place = retriever.places.get(place_id)
        if not place:
            raise HTTPException(404, "Place not found")
        return place

    return application


app = create_app()
