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

# test:
# 	python -m app.tests.utils.text_extracted_value

friedman:
	python app/tests/friedman.py


# convert:
# 	python -m app.ragas.utils.convert_synthetic_to_json