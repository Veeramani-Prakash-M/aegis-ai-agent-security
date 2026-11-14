.PHONY: install run test lint

install:
	python -m pip install -r requirements.txt

run:
	uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

test:
	pytest -q

lint:
	python -m compileall -q app tests
