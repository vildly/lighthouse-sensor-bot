┌───────────────────────────────────────────────────────────────────────────┐
│                           RAGAS/custom Metrics Explained                         │
├───────────────────────────┬───────────────────────────────────────────────┤
│ LenientFactualCorrectness │ Compares numerical values with tolerance      │
├───────────────────────────┼───────────────────────────────────────────────┤
│ SemanticSimilarity        │ Vector similarity between response and truth  │
├───────────────────────────┼───────────────────────────────────────────────┤
│ Faithfulness              │ How well response aligns with given context   │
├───────────────────────────┼───────────────────────────────────────────────┤
│ BleuScore                 │ Text similarity metric from NLP               │
├───────────────────────────┼───────────────────────────────────────────────┤
│ NonLLMStringSimilarity    │ String-based similarity without LLM           │
├───────────────────────────┼───────────────────────────────────────────────┤
│ RougeScore                │ Recall-oriented text similarity               │
├───────────────────────────┼───────────────────────────────────────────────┤
│ StringPresence            │ Checks if key strings are present             │
└───────────────────────────┴───────────────────────────────────────────────┘