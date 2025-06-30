# Lighthouse Sensor Bot

Repository for the Lighthouse sensor bot project.

This project initiated with the pre-study: "Large Language Models (LLMs) in Maritime Data Analysis and Decision Support."
Read more about it here: [Large Language Models (LLMs) can solve operational challenges](https://lighthouse.nu/en/whats-on/news/large-language-models-can-solve-operational-challenges)


Lighthouse Sensor Bot is a data analysis application that uses natural language queries to analyze maritime ferry data using agentic RAG. The system consists of:

- **Frontend**: Interface for submitting queries, and viewing results
- **Backend**: Flask server that processes queries with the help of an LLM as an agent
- **Database**: PostgreSQL database for storing query results and model evaluations

## Prerequisites

- **Docker** installed on your system.
- **OpenRouter API key** for accessing language model functionalities.
- **OpenAI API key** used when evaluating model responses using RAGAS metrics.
- **DeepSeek API key** optional, used when evaluating model responses using RAGAS metrics. (Much cheaper than OpenAI.)

**(You can choose between OpenAI and DeepSeek for evaluation, however, OpenAI key is required in either case for creating embeddings. If a DeepSeek key is provided in the backend .env file, it will be used for evaluation.)**

- **RAGAS App token** optional, used for uploading evaluation results to RAGAS app dashboard.

## Setup Instructions

To run the application as Docker containers,

### 1. Set Up Environment Variables

Create a `.env` file in the backend directory.

Copy the backend-example.env file to .env and update the variables.

For the frontend, create a `.env.development.local` file. (This can be omitted if you don't want to run the frontend in development mode from terminal.)

Copy the frontend-example.env.development.local file to .env.development.local and update the variable if needed.

Create a `.env` file in the root directory.

Copy the root-example.env file to .env and update the variables.

### 1.1 For ARM64 architecture

Change the Dockerfile in the backend directory to use the arm64 python image.

### 2. Start the Application

In the root directory, run:

```bash
docker-compose up -d --build
```
The PostgresQL database will be automatically initialized with the neccessary schema and data.
The frontend will be available at http://localhost:3000.

## Using the Application

1. Select a language model from the dropdown
2. Enter your question about ferry data (e.g., "What is the average speed of ferry Jupiter?")
3. View the response, including SQL queries executed

To evaluate a model, click the "Evaluate" button. This will run predefined queries and evaluate the model's performance using RAGAS metrics. You cannot submit your own queries when evaluating, due to the nature of the RAGAS evaluation requring a ground truth and reference context. 

In the Evaluation tab, you can see the average RAGAS scores for each model with graphs.

## Troubleshooting

If you encounter any issues, please do the following:

1. Ensure that the Docker containers are running properly.
2. Check the logs for any error messages.
3. Ensure that the environment variables are correctly set.


## Command Line Evaluation Testing (Locally)

The application includes powerful command-line tools for running and analyzing evaluation tests. These tools allow you to evaluate model performance and view results without using the web interface.

### Running Evaluation Tests

Navigate to the backend directory and use the evaluation test runner:

```bash
cd backend
python run_evaluation_tests.py
```

#### Test Options

**Interactive Model Selection:**
```bash
python run_evaluation_tests.py
# Lists available models and prompts for selection
```

**Run Tests for Specific Model:**
```bash
python run_evaluation_tests.py --model "google/gemini-2.5-flash-preview"
python run_evaluation_tests.py --model "anthropic/claude-3.7-sonnet"
python run_evaluation_tests.py --model "openai/gpt-4o-2024-11-20"
```

**Run Specific Test Cases:**
```bash
python run_evaluation_tests.py --tests 1,3,5        # Run specific test numbers
```

**Advanced Options:**
```bash
python run_evaluation_tests.py --model "gpt-4o" --runs 3 --max-retries 2 --tests 1,2,3
```

- `--runs`: Number of evaluation runs per test case (default: 1)
- `--max-retries`: Maximum retry attempts for failed tests (default: 1)
- `--test-cases`: Specific test cases to run (default: all 10 tests)

#### Example Test Run

```bash
$ python run_evaluation_tests.py --model "google/gemini-2.5-flash-preview" --tests 1,2,3

🚀 Starting Evaluation Tests
========================================
Model: google/gemini-2.5-flash-preview
Test Cases: 1-3 (3 tests)
Runs per test: 1
Max retries: 1

📊 Test Progress:
✅ Test 1/3: What is the average speed of ferry Jupiter? - PASSED
✅ Test 2/3: How many passengers did Vaxholmsleden carry in total? - PASSED
⚠️  Test 3/3: Which route has the highest carbon emissions? - RETRY 1
✅ Test 3/3: Which route has the highest carbon emissions? - PASSED

🎉 Evaluation Complete!
   Total Tests: 3
   Passed: 3
   Failed: 0
   Success Rate: 100%
```

### Viewing Test Results

Use the test results viewer to analyze evaluation data:

```bash
cd backend
python view_test_results.py
```

#### Results Viewing Options

**Recent Test Results (Default):**
```bash
python view_test_results.py                    # Show last 20 results
python view_test_results.py --limit 50         # Show last 50 results
```

**Model Performance Summary:**
```bash
python view_test_results.py --summary          # Aggregated metrics by model
```

**Detailed Results with Full Text:**
```bash
python view_test_results.py --detailed         # Show queries and responses
python view_test_results.py --detailed --limit 5  # Limit to 5 detailed results
```

**Filter by Specific Model:**
```bash
python view_test_results.py --model "google/gemini-2.5-flash-preview"
python view_test_results.py --model "openai/gpt-4o-2024-11-20" --limit 10
```

**Overall Statistics:**
```bash
python view_test_results.py --stats            # Test statistics and averages
python view_test_results.py --list-models      # List all tested models
```

#### Example Results Output

```bash
$ python view_test_results.py --summary

📊 Model Performance Summary (3 entries):
+--------------------------------+-------------+---------------------------+---------------------------+
| model_name                     | model_type  | query_evaluation_count    | avg_factual_correctness   |
+================================+=============+===========================+===========================+
| google/gemini-2.5-flash-prev  | proprietary | 18                       | 0.321                     |
| anthropic/claude-3.7-sonnet   | proprietary | 5                        | 0.456                     |
| openai/gpt-4o-2024-11-20      | proprietary | 12                       | 0.678                     |
+--------------------------------+-------------+---------------------------+---------------------------+
```

### Evaluation Metrics

The system evaluates models using RAGAS metrics:

- **Factual Correctness**: How factually accurate the response is
- **Semantic Similarity**: How semantically similar the response is to the ground truth
- **Context Recall**: How well the model uses retrieved context
- **Faithfulness**: How faithful the response is to the provided context
- **Token Usage**: Prompt, completion, and total tokens used

### API Access

You can also access evaluation functionality via API:

```bash
# Run evaluation via API
curl -X POST http://localhost:5001/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "google/gemini-2.5-flash-preview",
    "number_of_runs": 1,
    "max_retries": 1
  }'

# Get performance data
curl http://localhost:5001/api/model-performance
```

### Test Configuration

Test cases are defined in `backend/app/ragas/test_cases/synthetic_test_cases.json` and include:

1. Ferry speed analysis questions
2. Passenger traffic queries  
3. Route comparison questions
4. Environmental impact analysis
5. Operational efficiency metrics
6. Time-based traffic patterns
7. Cross-route comparisons
8. Data aggregation queries
9. Complex analytical questions
10. Multi-criteria analysis

Each test case includes:
- **Query**: The question to ask the model
- **Ground Truth**: Expected answer for evaluation
- **Contexts**: Reference information for context evaluation


### Common Issues

**Database Connection Errors:**
- Ensure PostgreSQL container is running: `docker-compose ps`
- Check database logs: `docker-compose logs postgres`

**Evaluation Test Failures:**
- Verify API keys are set correctly in `.env` files
- Check model availability with: `python view_test_results.py --list-models`
- Review test logs for specific error messages

**Performance Issues:**
- Large models may take several minutes per test
- Consider using `--test-cases` to run smaller test subsets
- Monitor token usage with `--detailed` results view

## Known issues

Every now and then a model will try to use a tool that doesn't exist or other errors from the LLMwill occur. Currently this results in a 500 status code as response. We are working on a more graceful solution.


