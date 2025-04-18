# lighthouse

## Overview

Lighthouse is a data analysis application that uses natural language queries to analyze maritime ferry data using agentic RAG. The system consists of:

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

For the frontend, create a `.env.development.local` file. (This can be omitted if you don't want to run the frontend in development mode.)

Copy the frontend-example.env.development.local file to .env.development.local and update the variable if needed.

Create a `.env` file in the root directory.

Copy the root-example.env file to .env and update the variables.

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