FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

# CMD ["gunicorn", "-c", "gunicorn_config.py", "app.main:app"]
CMD ["python", "-m", "app.main"]
