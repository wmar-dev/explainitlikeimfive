.PHONY: install install-frontend install-backend run run-backend run-frontend clean

install: install-backend install-frontend

install-backend:
	uv sync

install-frontend:
	cd frontend && npm install

run-backend:
	uv run python backend/app.py

run-frontend:
	cd frontend && npm start

run:
	@echo "Run backend and frontend in separate terminals:"
	@echo "  make run-backend"
	@echo "  make run-frontend"

clean:
	rm -rf frontend/node_modules frontend/build .venv __pycache__ backend/__pycache__
