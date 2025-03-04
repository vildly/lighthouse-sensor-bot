# Start the application (Development only)
dev:
	python -m app.app

# Freeze dependencies
freeze:
	pip freeze > requirements.txt

# Install dependencies
i:
	pip install -r requirements.txt

# Clean temporary files
clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache

eval:
	python -m app.ragas.scripts.ferries_ragas_evaluation