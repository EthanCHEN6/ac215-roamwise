"use strict";
const $ = (id) => document.getElementById(id);
let saved;
try {
  saved = JSON.parse(localStorage.getItem("roamwise-saved-v1") || "[]");
  if (!Array.isArray(saved)) saved = [];
} catch {
  saved = [];
}
const labels = {
  culture: "Arts & culture",
  outdoors: "Outdoors & landmarks",
  food: "Food & coffee",
  lodging: "Places to stay",
};
function el(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function persist() {
  localStorage.setItem("roamwise-saved-v1", JSON.stringify(saved));
  $("saved-count").textContent = saved.length;
  renderSaved();
}
function renderSaved() {
  $("saved-list").replaceChildren();
  if (!saved.length)
    $("saved-list").append(el("p", "Save a place from your search results."));
  saved.forEach((p) => {
    const row = el("div", undefined, "saved-row");
    row.append(el("span", `${p.name} · ${p.city}`));
    const remove = el("button", "Remove", "text-button");
    remove.addEventListener("click", () => {
      saved = saved.filter((x) => x.place_id !== p.place_id);
      persist();
      document.querySelectorAll(".save").forEach((b) => {
        if (b.dataset.placeId === p.place_id) {
          b.textContent = "Save +";
          b.setAttribute("aria-pressed", "false");
        }
      });
    });
    row.append(remove);
    $("saved-list").append(row);
  });
}
async function showDetail(place) {
  const body = $("detail-body");
  body.replaceChildren(el("p", "Loading place details…"));
  $("detail").showModal();
  try {
    const response = await fetch(
      "/api/places/" + encodeURIComponent(place.place_id),
    );
    if (!response.ok) throw new Error("Place details are unavailable.");
    const data = await response.json();
    body.replaceChildren(
      el("h2", data.name),
      el("p", `${labels[data.category]} · ${data.city}`),
      el("p", data.address),
    );
    body.append(
      el("h3", "Historical information"),
      el(
        "p",
        `Rating: ${data.rating ?? "Unknown"} / 5 · ${data.review_count.toLocaleString()} reviews in the source metadata`,
      ),
      el("p", `Price: ${data.price ?? "Unknown"}`),
      el(
        "p",
        "Hours: " +
          (data.historical_hours
            ? JSON.stringify(data.historical_hours)
            : "Unknown"),
      ),
    );
    body.append(el("h3", "Retrieved sources"));
    place.evidence.forEach((c) => {
      body.append(
        el("p", c.text),
        el(
          "p",
          `[${c.citation}] ${c.kind} · ${c.source_file}, line ${c.source_line} · chunk ${c.chunk_id}`,
          "detail-source",
        ),
      );
    });
    body.append(
      el(
        "p",
        "These records are historical. They do not establish whether this place is open today.",
        "detail-source",
      ),
    );
    if (data.source_url) {
      const link = el("a", "Check this place on Google Maps ↗");
      link.href = data.source_url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      body.append(link);
    }
  } catch (error) {
    body.replaceChildren(el("p", error.message));
  }
}
function renderPlace(place, method) {
  const card = el("article", undefined, "place");
  card.append(el("span", String(place.rank).padStart(2, "0"), "rank"));
  const content = el("div");
  const top = el("div", undefined, "place-top");
  top.append(el("h3", place.name));
  const save = el(
    "button",
    saved.some((p) => p.place_id === place.place_id) ? "Saved ✓" : "Save +",
    "save",
  );
  save.dataset.placeId = place.place_id;
  save.setAttribute(
    "aria-pressed",
    String(saved.some((p) => p.place_id === place.place_id)),
  );
  save.addEventListener("click", () => {
    if (saved.some((p) => p.place_id === place.place_id))
      saved = saved.filter((p) => p.place_id !== place.place_id);
    else
      saved.push({
        place_id: place.place_id,
        name: place.name,
        city: place.city,
        address: place.address,
        source_url: place.source_url,
      });
    persist();
    const chosen = saved.some((p) => p.place_id === place.place_id);
    save.textContent = chosen ? "Saved ✓" : "Save +";
    save.setAttribute("aria-pressed", String(chosen));
  });
  top.append(save);
  content.append(
    top,
    el(
      "p",
      `${labels[place.category]} / ${place.city} / ${place.rating ?? "—"} ★ historical rating`,
      "place-meta",
    ),
    el("p", place.address, "place-address"),
  );
  const source =
    place.evidence.find((c) => c.kind === "review") || place.evidence[0];
  if (source) {
    const quote = el(
      "blockquote",
      source.text.length > 270 ? source.text.slice(0, 270) + "…" : source.text,
      "quote",
    );
    quote.append(
      el(
        "small",
        `[${source.citation}] ${source.kind === "review" ? "Review excerpt" : "Place metadata"} · Google Local 2021`,
      ),
    );
    content.append(quote);
  }
  const bottom = el("div", undefined, "place-footer");
  const more = el("button", "Details & sources ↗", "text-button");
  more.addEventListener("click", () => showDetail(place));
  bottom.append(
    more,
    el(
      "span",
      method === "semantic"
        ? `Similarity ${place.score.toFixed(3)} · not a probability`
        : `Adjusted rating ${place.score.toFixed(2)} / 5`,
      "score",
    ),
  );
  content.append(bottom);
  card.append(content);
  return card;
}
async function search() {
  const query = $("query").value.trim();
  if (query.length < 3) {
    $("message").textContent = "Enter at least three characters.";
    return;
  }
  const button = $("search-button");
  button.disabled = true;
  button.textContent = "Searching sources…";
  $("message").classList.remove("error");
  $("message").textContent = "Reading the local index…";
  $("results").replaceChildren();
  $("context-panel").hidden = true;
  try {
    const response = await fetch("/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        city: $("city").value || null,
        category: $("category").value || null,
        method: $("method").value,
        top_k: 5,
      }),
    });
    if (!response.ok)
      throw new Error(
        response.status === 422
          ? "Please check your search inputs."
          : response.status === 429
            ? "The demo is busy. Wait a few seconds and search again."
            : "Search is temporarily unavailable. Please try again later.",
      );
    const data = await response.json();
    $("results-title").textContent = data.results.length
      ? `${data.results.length} places to explore`
      : "No places found";
    $("message").textContent = data.results.length
      ? `${data.elapsed_ms.toFixed(0)} ms · ${data.method === "semantic" ? "Ranked by text similarity" : "Ranked by category and adjusted rating"} · ${data.dataset_id}`
      : "Try another area or remove the type filter.";
    data.results.forEach((p) =>
      $("results").append(renderPlace(p, data.method)),
    );
    $("context").textContent = data.context;
    $("context-panel").hidden = !data.results.length;
  } catch (error) {
    $("message").textContent = error.message;
    $("message").classList.add("error");
  } finally {
    button.disabled = false;
    button.textContent = "Find places ↗";
  }
}
$("search-form").addEventListener("submit", (event) => {
  event.preventDefault();
  search();
});
$("close-detail").addEventListener("click", () => $("detail").close());
$("saved-toggle").addEventListener("click", () => {
  $("saved-panel").hidden = !$("saved-panel").hidden;
  if (!$("saved-panel").hidden)
    $("saved-panel").scrollIntoView({ behavior: "smooth" });
});
const examples = {
  outdoors: ["A park for an outdoor walk", "Boston"],
  food: ["Coffee shop for breakfast", "Cambridge"],
  lodging: ["A hotel for a weekend visit", "Boston"],
};
document.querySelectorAll("[data-example]").forEach((button) =>
  button.addEventListener("click", () => {
    const [query, city] = examples[button.dataset.example];
    $("query").value = query;
    $("city").value = city;
    $("category").value = "";
    search();
  }),
);
$("export").addEventListener("click", () => {
  const content =
    "RoamWise shortlist\nHistorical source data through September 2021. Verify current information.\n\n" +
    saved
      .map(
        (p, i) =>
          `${i + 1}. ${p.name} — ${p.city}\n${p.address}\n${p.source_url || ""}`,
      )
      .join("\n\n");
  const url = URL.createObjectURL(new Blob([content], { type: "text/plain" }));
  const link = el("a");
  link.href = url;
  link.download = "roamwise-shortlist.txt";
  link.click();
  URL.revokeObjectURL(url);
});
persist();
fetch("/api/status")
  .then((r) => {
    if (!r.ok) throw new Error();
    return r.json();
  })
  .then((data) => {
    $("dataset-status").textContent =
      `${data.dataset.counts.places} places · index ready`;
  })
  .catch(() => {
    $("dataset-status").textContent = "Index unavailable";
  });
