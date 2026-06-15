.PHONY: help setup install dev build preview typecheck clean

help:
	@echo "Frontend targets:"
	@echo "  setup      — install dependencies (first-time setup)"
	@echo "  install    — install npm dependencies"
	@echo "  dev        — start Vite dev server on :5173 (proxies /api to :8000)"
	@echo "  build      — production build into dist/"
	@echo "  preview    — preview the production build locally"
	@echo "  typecheck  — run TypeScript compiler check (no emit)"
	@echo "  clean      — remove node_modules and dist/"

setup: install
	@echo ""
	@echo "  Ready. Run 'make dev' to start the frontend."
	@echo "  The backend must be running on :8000 for API calls to work."

install:
	npm install

dev:
	npm run dev

build:
	npm run build

preview:
	npm run preview

typecheck:
	npx tsc --noEmit

clean:
	rm -rf node_modules dist

.DEFAULT_GOAL := help
