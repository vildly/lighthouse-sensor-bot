# LLM Evaluation Framework

This is the backend for Lighhouse Bot, a system for evaluating LLM-powered agentic RAG data analysis.

## Introduction

This evaluation framework tests and measures the performance of LLM-based data analysis agents. By running standardized test cases through your agent and analyzing responses using RAGAS/custom metrics, it assessess the accuracy and quality of agent outputs.

## System Architecture

The evaluation system follows a structured pipeline as visualized in this [high-level flow diagram](docs/e2e-flow-high-level.md):

The main components include:

- **API Layer**: HTTP endpoints for triggering evaluations
- **Orchestration Layer**: Test scheduling and management
- **Execution Layer**: Agent initialization and query processing
- **Evaluation Layer**: Metrics calculation
- **Storage Layer**: Database persistence of results
- **Reporting Layer**: Results aggregation and formatting

## Evaluation Process

The evaluation follows this process:

1. **Test Initialization** - API endpoint receives evaluation request with model parameters
   ```
   POST /evaluate
   {
     "model_id": "gpt-4",
     "number_of_runs": 3,
     "max_retries": 2
   }
   ```

2. **Agent Processing** - Each test case is run through the agent (see [evaluation flow](docs/evaluation-flow.md))
   ![Evaluation Flow](docs/evaluation-flow.md)

3. **Evaluation** - Responses are evaluated using multiple metrics
   ![Metrics](docs/metrics.md)

4. **Results Storage** - All results are stored in a containerized SQL database for analysis

5. **Results Reporting** - Summary metrics and individual test results returned

## Metrics

The framework uses the following metrics to evaluate responses:

| Metric | Description |
|--------|-------------|
| LenientFactualCorrectness | Compares numerical values with tolerance |
| SemanticSimilarity | Vector similarity between response and truth |
| Faithfulness | How well response aligns with given context |
| BleuScore | Text similarity metric from NLP |
| NonLLMStringSimilarity | String-based similarity without LLM |
| RougeScore | Recall-oriented text similarity |
| StringPresence | Checks if key strings are present |

All metrics are scored between 0 and 1, where higher is better.

## Test Queries

Test queries and ground truths are stored in JSON format in [this file.](../app/ragas/test_cases/synthetic_test_cases.json)

## Ground truth verification

Ground truth verification is done in [this file.](../ValidateSyntheticQuestions.ipynb)

## Agent

Flow diagram of the agent initialization:
![Agent Flow](docs/agent-init.md)

The agent is defined in [this file.](../app/services/agent.py)

Semantic Model is defined in [this file.](../data/semantic_model.json)

## Dataset

The dataset is defined in the following files:

[Technical information about the ferries](../data/ferries.json)

[Description of routes](../data/route_descriptions.json)

[Historical trip data](../data//ferry_trips_data.csv)