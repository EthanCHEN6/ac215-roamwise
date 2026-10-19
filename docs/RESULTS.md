> Earlier retrieval-only build. See [RAG update](RAG.md) and [new verification](RAG_RESULTS.md) for the current release.

# MS2 run results

Recorded on 2026-10-16 using Docker Desktop, Linux containers and CPU inference. Source and implementation versions are in the evidence manifests and uv lockfiles.

| Data stage | Observed count |
|---|---:|
| Metadata rows scanned | 92,520 |
| Review rows scanned | 10,447,007 |
| Eligible unique places | 4,114 |
| Selected places | 500 |
| Sampled reviews | 3,000 |
| Indexed chunks | 3,976 |

Dataset: `boston-36bb6d7b74e39df3`. Index: `80e7efec48cc96a7`. First indexing took 262.428 seconds, including the encoder download. The final one-command replay reused the verified dataset and index.

## Fixed query comparison

Both methods received the same 20 queries and city filters, without category filters. Each query has one expected broad category. The metric counts matching categories among the first five returned places, with missing results counting as misses.

| Method | Mean category hits @5 | Median HTTP latency | p95 HTTP latency | Duplicate places |
|---|---:|---:|---:|---:|
| Category + rating | 0.95 | 3.54 ms | 4.39 ms | 0 |
| MiniLM retrieval | 0.92 | 95.98 ms | 122.23 ms | 0 |

This is a smoke benchmark, not human Precision@5. Category words in the queries favor the keyword baseline. Latency was measured sequentially from the evaluation container after the API warmed the encoder; it is not a load test.

The baseline missed “lodging near a university”: keyword votes tied and the current tie order chose outdoors. Semantic retrieval mixed categories on five cases, including coffee shops and aquariums. Do not tune on these cases and then present the same set as independent validation.

In the saved art-museum example, semantic retrieval placed Harvard Art Museums first and returned review-source citations. A browser comparison of the same intent put The Brattle Theatre first under the broad category/rating baseline. This illustrates a useful distinction that the category-only metric does not measure.

## Checks

18 tests passed in the uv test container. They cover source checksum rejection, geographic and closure filters, missing data, chunk overlap, contact redaction, API input validation, empty results, place lookup and retrieval deduplication/citations. One dependency deprecation warning remains; it does not fail the tests.

Browser checks verified real search responses, source details, baseline switching, saved places after reload and shortlist export. See `evidence/` for the observed outputs. These checks do not establish current-world accuracy, complete browser-test coverage or a production SLA.

Next experiment: collect independent relevance judgments for realistic multi-constraint queries, retain a held-out set, and compare a trained reranker against both existing methods.
