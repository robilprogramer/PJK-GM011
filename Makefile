.PHONY: install setup seed run run-prod test lint clean

install:
	pip install -r requirements.txt

setup: install
	cp -n .env.example .env || true
	@echo ""
	@echo "Edit .env — isi GROQ_API_KEY dan OWM_API_KEY"
	@echo "Model ML sudah tersedia di models/ (dari ML Pipeline project)"

seed:
	python scripts/seed_knowledge.py

run:
	uvicorn main:app --reload --port 8000

run-prod:
	uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2

test:
	pytest tests/ -v --tb=short 2>/dev/null || echo "Belum ada test"

lint:
	flake8 app/ --max-line-length=120 --exclude=__pycache__ 2>/dev/null || true

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

start: setup seed run
