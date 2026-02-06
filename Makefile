.PHONY: install test test-unit test-integration lint format clean ingest run docker-up docker-down

# Install dependencies
install:
	pip install -e ".[dev]"

# Run all tests
test:
	pytest tests/ -v

# Run unit tests only
test-unit:
	pytest tests/unit/ -v

# Run integration tests only
test-integration:
	pytest tests/integration/ -v

# Run tests with coverage
test-coverage:
	pytest --cov=app --cov-report=html --cov-report=term-missing tests/
	@echo "Coverage report generated in htmlcov/"

# Lint code
lint:
	ruff check app/

# Format code
format:
	ruff format app/

# Clean build artifacts
clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Ingest knowledge base documents
ingest:
	python app/rag/ingest.py

# Run the Streamlit application locally
run:
	streamlit run app/main.py

# Start Docker Compose services
docker-up:
	docker-compose up --build -d

# Stop Docker Compose services
docker-down:
	docker-compose down

# View Docker logs
docker-logs:
	docker-compose logs -f finnie-app

# Pull Ollama embedding model
ollama-setup:
	ollama pull nomic-embed-text

# Run a quick health check
health-check:
	@echo "Checking services..."
	@curl -s http://localhost:8501 > /dev/null && echo "✓ Streamlit UI is running" || echo "✗ Streamlit UI is not running"
	@curl -s http://localhost:6007 > /dev/null && echo "✓ Phoenix is running" || echo "✗ Phoenix is not running"
	@curl -s http://localhost:11434 > /dev/null && echo "✓ Ollama is running" || echo "✗ Ollama is not running"

# Full development setup
dev-setup: install ollama-setup ingest
	@echo "Development environment is ready!"
	@echo "Run 'make run' to start the application"
