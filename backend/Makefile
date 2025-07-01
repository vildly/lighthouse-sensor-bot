# Start the application (Development only)
dev:
	.venv/bin/python -m app.app

# Freeze dependencies
freeze:
	.venv/bin/pip freeze > requirements.txt

# Create virtual environment if not exists
venv:
	@test -d .venv || python3 -m venv .venv

# Install dependencies inside the virtual environment
i: venv
	.venv/bin/pip install -r requirements.txt

# Run everything in one command!!!: install + start
run: i dev





# Clean temporary files
clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache


# COMMENTED OUT - Evaluation Mode functionality
# friedman:
# 	python app/tests/friedman.py




