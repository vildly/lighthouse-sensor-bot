┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│ API     │     │ Query   │     │ Execute │     │ Test    │     │ Run     │
│ Endpoint├────►│ with    ├────►│ Test    ├────►│ Run     ├────►│ Test    │
│         │     │ Eval    │     │ Runs    │     │ Manager │     │ Case    │
└─────────┘     └─────────┘     └─────────┘     └─────────┘     └────┬────┘
                                                                      │
                                                                      ▼
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│ Save to │     │ RAGAS   │     │ Agent   │     │ Extract │     │ Process │
│ Database│◄────┤ Evaluate│◄────┤ Response│◄────┤ SQL &   │◄────┤ Query   │
│         │     │         │     │         │     │ Tokens  │     │ Internal│
└─────────┘     └─────────┘     └─────────┘     └─────────┘     └─────────┘
     │
     │
     ▼
┌─────────┐     ┌─────────┐
│ Format  │     │ Return  │
│ Results ├────►│ API     │
│         │     │ Response│
└─────────┘     └─────────┘