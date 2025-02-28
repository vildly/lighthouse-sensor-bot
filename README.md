# lighthouse-sensor-bot

# How to

Welcome to the setup guide for this project! This application leverages the power of Retrieval-Augmented Generation (RAG) using the phi framework, providing intelligent responses informed by a knowledge database which in this example consists of a 14-page document filled with delicious Thai recipes. From classic curries to refreshing salads, these recipes incorporate authentic Thai ingredients and techniques, offering a rich source for generating culinary insights. This document is central to the application's ability to deliver contextually relevant and mouth-watering recommendations.

Harness the wisdom of traditional Thai cuisine combined with cutting-edge AI to bring flavorful, intelligent responses to your queries.

## Overview

This app consists of:

- **Frontend**: A user-friendly interface for asking questions.
- **Backend**: A Flask server that processes requests using AI and a knowledge database.
- **Database**: A PostgreSQL database managed by `phidata` to store and retrieve information efficiently.

## Prerequisites

- **Docker** installed on your system.
- **Node.js** and **npm** installed for running the frontend.
- **Python** installed for the backend.
- **OpenAI API key** for accessing language model functionalities.

## Setup Instructions

### 1. Set Up the Database

Run the following command to start the PostgreSQL database container using `pgvector`:

```bash
docker run -d \
  -e POSTGRES_DB=ai \
  -e POSTGRES_USER=ai \
  -e POSTGRES_PASSWORD=ai \
  -e PGDATA=/var/lib/postgresql/data/pgdata \
  -v pgvolume:/var/lib/postgresql/data \
  -p 5532:5432 \
  --name pgvector \
  phidata/pgvector:16
```

### 2. Start the Frontend

Navigate to the `frontend` directory and install dependencies:

```bash
cd frontend
npm install
```

To start the frontend server:

```bash
npm run dev
```

This will start the frontend server at `http://localhost:3000`.

### 3. Start the Backend

Navigate to the `backend` directory and create a virtual environment:

```bash
cd backend
python -m venv venv
```

Activate the virtual environment:

- **On macOS/Linux**:
  ```bash
  source venv/bin/activate
  ```
- **On Windows**:
  ```bash
  .\venv\Scripts\activate
  ```

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Run the backend server:

```bash
python app.py
```

### 4. Set Up OpenAI API Key

For the backend to access OpenAI's services, you need to set your API key:

- **On macOS/Linux**:
  ```bash
  export OPENAI_API_KEY=sk-<your_api_key>
  ```
- **On Windows**:
  ```cmd
  set OPENAI_API_KEY=sk-<your_api_key>
  ```

Replace `<your_api_key>` with your actual OpenAI API key.

### 5. Access the Application

Open your web browser and navigate to:

```
http://localhost:3000
```

Enter your question into the input field and press "Send" to receive an AI-generated response.

### Troubleshooting

- Ensure all services (frontend, backend, and database) are running.
- Check network connectivity and API key validity if you encounter errors.
- Review console logs for detailed error messages.

This setup guide should help you initialize and use your application efficiently. Enjoy asking and answering questions with the power of AI!
