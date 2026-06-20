.PHONY: test test-coverage install run

install:
	pip install -r requirements.txt

test:
	pytest -v

test-coverage:
	pytest --cov=app --cov-report=term-missing --cov-report=html:coverage --cov-fail-under=70 -v

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
