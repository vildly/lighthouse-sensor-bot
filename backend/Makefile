# Start the application (Development only)
dev:
	python -m app.app

# Freeze dependencies
freeze:
	pip freeze > requirements.txt

# Install dependencies
i:
	python -m pip install -r requirements.txt

# Clean temporary files
clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache

test:
	python -m app.tests.utils.text_extracted_value

# eval:
# 	python -m app.ragas.scripts.ragas_tests

# eval-s:
# 	python -m app.ragas.scripts.synthetic_ragas_tests --model_id="openai/gpt-4o-2024-11-20"

convert:
	python -m app.ragas.utils.convert_synthetic_to_json