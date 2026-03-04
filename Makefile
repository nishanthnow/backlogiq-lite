.PHONY: help dev-backend dev-frontend install-backend install-frontend test

help:
	@echo "BacklogIQ Lite - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  dev-backend         - Run FastAPI backend with auto-reload (port 8000)"
	@echo "  dev-frontend        - Run React frontend with Vite (port 5173)"
	@echo "  install-backend     - Install backend dependencies"
	@echo "  install-frontend    - Install frontend dependencies"
	@echo "  test                - Run tests"

dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

install-backend:
	cd backend && pip install -r requirements.txt

install-frontend:
	cd frontend && npm install
