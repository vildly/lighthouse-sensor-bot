FROM python:3.11-slim
# For ARM64 architecture, use the following line instead
# FROM --platform=linux/arm64 python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt


# CMD ["gunicorn", "-c", "gunicorn_config.py", "app.app:app"]
CMD ["python", "-m", "app.app"]
