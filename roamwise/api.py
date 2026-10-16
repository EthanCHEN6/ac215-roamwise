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


def create_app(engine=None):
    @asynccontextmanager
    async def lifespan(application):
        if engine is None:
            from roamwise.retrieval import Retriever

            application.state.engine = Retriever()
        yield

    application = FastAPI(title="RoamWise", version="0.1.0", lifespan=lifespan)
    application.state.engine = engine

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
        return {"dataset": retriever.dataset, "index": retriever.index}

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
