# Presentation notes and TF questions

## Short presentation

RoamWise helps users draft short trips in Greater Boston. Our earlier version retrieved places and source passages. This version adds a language model before and after retrieval.

First, the model turns preferences into a search for each selected interest. The server applies city and category filters. It retrieves passages from Chroma and lets the user select places. The recommendation filters keep the same interest names as the form. A place can match more than one search.

Next, the server retrieves context again. The model produces a structured itinerary with citations. We check place IDs, citation membership, duplicate stops and the daily schedule. We allow one repair attempt. If it fails, we return an error.

Our historical database contains 500 places. Its sources end in 2021. Users must check current hours and prices separately. Travel times are estimates. We do not claim that routes are optimal or that every generated statement is correct.

All Python services use uv and run in containers. Cloud Run hosts the website and API, so teammates can use the app without the owner's laptop. We record dataset, index, prompt and model versions for inspection.

## Demo sequence

1. Select Cambridge, one day, History, Museums, Food and Nature.
2. Show the matching filters. Open one place and its historical source.
3. Select two or three stops and generate an itinerary.
4. Open a citation and the generation record. Explain the limits of automatic validation.

## Likely questions

| Question | Answer |
|---|---|
| Where is RAG? | Retrieved passages enter the generation prompt. The output cites those passages. Vector search alone was only the retrieval component. |
| Why not ask Gemini directly? | Retrieval limits candidate places and exposes the evidence. We still need to assess how well the model uses it. |
| Did you train a model? | No. We use pretrained MiniLM for embeddings and Gemini for generation. |
| Why separate History and Museums? | They are distinct user interests. Both search the culture index, but use separate queries and keep separate result filters. |
| Does a matched interest prove relevance? | No. It records which search retrieved the place. Human relevance labels are still needed. |
| Why a 0.25 similarity cutoff? | It is an initial threshold. It is not a probability and has not been calibrated with human labels. |
| How do you reduce hallucinations? | Bounded context, structured output, place and citation checks, and one repair attempt. Semantic entailment is not automatically verified. |
| Are prices and travel times reliable? | Current prices are not verified. Transfers use straight-line distance and assumed speeds. |
| Does the database update itself? | An operator runs snapshot audits and Google place-ID discovery. Current details are fetched on demand. Full review refresh is not implemented. |
| Are there two agents? | There are two connected components. Data maintenance is a controlled job; trip planning uses bounded LLM orchestration. |
| Do passing tests prove recommendation quality? | No. Tests check program behavior. Independent human evaluation remains future work. |
| How are costs controlled? | Scale to zero, one instance maximum, bounded concurrency and request limits. These are not hard spending caps. |

## Questions for the TF

- Is the LLM/RAG assessment path appropriate for this hybrid project?
- Is the historical pilot sufficient for MS2, with current details checked separately?
- Which human evaluation should we prioritize next: retrieval relevance, claim support or itinerary usefulness?
