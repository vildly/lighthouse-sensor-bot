┌────────────────────┐     ┌────────────────────┐     ┌────────────────────┐
│ process_query      │     │ Setup Log Capture  │     │ Get Data Analyst   │
│ _internal()        ├────►│ WebSocket Logger   ├────►│ with Model ID      │
└────────────────────┘     └────────────────────┘     └──────────┬─────────┘
                                                                  │
                                                                  ▼
┌────────────────────┐     ┌────────────────────┐     ┌────────────────────┐
│ Load Semantic      │     │ Create DuckDb      │     │ Initialize Agent   │
│ Model Definition   ├────►│ Tools & Functions  ├────►│ with System Prompt │
└────────────────────┘     └────────────────────┘     └──────────┬─────────┘
                                                                  │
                                                                  ▼
┌────────────────────┐     ┌────────────────────┐     ┌────────────────────┐
│ Agent.run()        │     │ Extract SQL from   │     │ Format Response as │
│ Processes Question ├────►│ Log & Run Queries  ├────►│ Markdown with SQL  │
└────────────────────┘     └────────────────────┘     └──────────┬─────────┘
                                                                  │
                                                                  ▼
                                                     ┌────────────────────┐
                                                     │ Return Results &   │
                                                     │ Token Usage        │
                                                     └────────────────────┘