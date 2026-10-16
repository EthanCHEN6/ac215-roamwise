"use strict";
const labels = {
  culture: "Arts & culture",
  outdoors: "Outdoors & landmarks",
  food: "Food & coffee",
  lodging: "Places to stay",
};
let examples = [],
  selected = "art",
  recordedAt = "";
const byId = (id) => document.getElementById(id);
function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function render() {
  const example = examples.find((x) => x.id === selected);
  if (!example) return;
  const method = byId("method").value,
    data = example.methods[method];
  byId("query").textContent = `“${example.query}” · ${example.city}`;
  byId("method-note").textContent =
    method === "semantic"
      ? "Ranked by text similarity"
      : "Ranked by category and adjusted rating";
  byId("results").replaceChildren();
  data.results.forEach((place) => {
    const card = element("article", undefined, "result");
    card.append(
      element("span", String(place.rank).padStart(2, "0"), "rank"),
      element("h3", place.name),
      element("p", `${labels[place.category]} / ${place.city}`, "meta"),
      element("p", place.address, "address"),
    );
    const source =
      place.evidence.find((x) => x.kind === "review") || place.evidence[0];
    if (source) card.append(element("blockquote", source.text + "…"));
    card.append(
      element(
        "p",
        method === "semantic"
          ? `Similarity ${place.score.toFixed(3)} · not a probability`
          : `Adjusted historical rating ${place.score.toFixed(2)} / 5`,
        "score",
      ),
    );
    const details = element("details");
    details.append(element("summary", "View source record"));
    place.evidence.forEach((source) => {
      details.append(
        element("p", source.text + "…", "source-text"),
        element(
          "p",
          `[${source.citation}] ${source.kind} · ${source.source_file}, line ${source.source_line}`,
        ),
      );
    });
    details.append(
      element(
        "p",
        `Dataset ${data.dataset_id}. Excerpts shortened to at most 25 words.`,
      ),
    );
    if (place.source_url) {
      const map = element("a", "Check on Google Maps ↗");
      map.href = place.source_url;
      map.target = "_blank";
      map.rel = "noopener noreferrer";
      details.append(map);
    }
    card.append(details);
    byId("results").append(card);
  });
  byId("record-note").textContent =
    `Recorded ${recordedAt.slice(0, 10)} · real API results, shortened excerpts · this is a replay, not a new search.`;
}
document.querySelectorAll("[data-example]").forEach((button) =>
  button.addEventListener("click", () => {
    selected = button.dataset.example;
    document
      .querySelectorAll("[data-example]")
      .forEach((x) => x.setAttribute("aria-pressed", String(x === button)));
    render();
  }),
);
byId("method").addEventListener("change", render);
fetch("examples.json")
  .then((r) => {
    if (!r.ok) throw new Error();
    return r.json();
  })
  .then((data) => {
    examples = data.examples;
    recordedAt = data.recorded_at;
    render();
  })
  .catch(() => {
    byId("query").textContent =
      "Recorded examples could not load. Please reload or open the source repository.";
  });
// A public link record allows the live session to change independently of this static page.
fetch(
  "https://raw.githubusercontent.com/EthanCHEN6/ac215-roamwise/main/share/live.json",
  { cache: "no-store", signal: AbortSignal.timeout(5000) },
)
  .then((r) => {
    if (!r.ok) throw new Error();
    return r.json();
  })
  .then((data) => {
    const url = new URL(data.url);
    if (
      url.protocol !== "https:" ||
      !url.hostname.endsWith(".trycloudflare.com")
    )
      return;
    document.querySelectorAll(".live-link").forEach((a) => (a.href = url.href));
  })
  .catch(() => {});
