# RAGFlow Project Instructions for AI Agents

This file provides context, build instructions, and coding standards for working with the RAGFlow project.

## 1. Project Overview

RAGFlow is an open-source RAG (Retrieval-Augmented Generation) engine based on deep document understanding. It is a full-stack application with a Python backend and a React/TypeScript frontend.

- **Backend**: Python 3.10-3.12 (Flask/Quart)
- **Frontend**: TypeScript, React, UmiJS, Ant Design
- **Architecture**: Microservices based on Docker
- **Package Manager**: uv (Python), npm (Frontend)

## 2. Directory Structure

```
api/              # Backend API server (Flask/Quart)
  apps/           # API Blueprints (kb_app, dialog_app, document_app, etc.)
  db/             # Database models and services
rag/              # Core RAG logic
  llm/            # LLM, Embedding, and Rerank model abstractions
  flow/           # RAG pipeline (chunking, parsing, tokenization)
  graphrag/       # Knowledge graph construction and querying
deepdoc/          # Document parsing and OCR modules
agent/            # Agentic reasoning components
  templates/      # Pre-built agent workflows
  sandbox/        # Code execution sandbox
web/              # Frontend application (React + UmiJS)
docker/           # Docker deployment configurations
sdk/              # Python SDK
test/             # Backend tests (unit_test, testcases)
```

## 3. Agent Workflow

### Common Task Workflow

1. **Understand the codebase**: Use glob and grep to find relevant files
2. **Read context**: Use read to examine files before editing
3. **Make changes**: Use edit to modify files, write to create new files
4. **Test changes**: Run appropriate tests to verify
5. **Verify code quality**: Run linting and formatting tools

### Important Guidelines

- **ALWAYS read a file before editing it** - Understand the existing code style and patterns first
- **Match existing conventions** - Follow the code style of the surrounding code
- **Keep responses concise** - Answer directly without unnecessary preamble
- **Use explicit paths** - Always use absolute paths when referring to files
- **Run linting after changes** - Always run ruff and npm run lint after making changes

## 4. Build Instructions

### Backend (Python)

```bash
# Install system dependencies for lxml (required before installing Python packages):
# Ubuntu/Debian: sudo apt-get install libxml2-dev libxslt-dev python3-dev build-essential

# Install Python dependencies
uv sync --python 3.12 --all-extras
uv run download_deps.py
pre-commit install

# Start dependent services (MySQL, ES/Infinity, Redis, MinIO)
docker compose -f docker/docker-compose-base.yml up -d

# Run backend
source .venv/bin/activate
export PYTHONPATH=$(pwd)
bash docker/launch_backend_service.sh
```

### Frontend (TypeScript/React)

```bash
cd web
npm install
npm run dev        # Runs on port 8000
```

### Docker Deployment

```bash
cd docker
docker compose -f docker-compose.yml up -d
```

## 5. Testing Instructions

### Backend Tests

The project uses pytest with the following test types:

- **Unit Tests**: `/test/unit_test/` - Fast, isolated tests
- **Integration Tests**: `/test/testcases/` - Full API integration tests
- **HTTP API Tests**: `/test/testcases/test_http_api/`
- **Web API Tests**: `/test/testcases/test_web_api/`

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest test/test_api.py

# Run tests with markers
uv run pytest -m unit      # Unit tests only
uv run pytest -m integration

# Run with verbose output
uv run pytest -v

# Run specific test class
uv run pytest test/unit_test/api/apps/test_kb_app.py::TestKBApp
```

Test markers used in this project:
- `unit` - Unit tests
- `integration` - Integration tests

### Frontend Tests

```bash
cd web
npm run test        # Jest tests
npm run lint        # ESLint
```

### Linting & Formatting

```bash
# Python (ruff)
ruff check .        # Check for issues
ruff format .       # Format code

# Frontend
cd web
npm run lint        # ESLint
npm run lint:fix    # ESLint with auto-fix
```

## 6. Code Review Guidelines

### Before Submitting Changes

1. **Run linting**:
   ```bash
   ruff check .
   ruff format .
   ```

2. **Run tests** to ensure nothing is broken

3. **Review your changes**:
   - Check for hardcoded secrets/keys
   - Ensure proper error handling
   - Follow existing naming conventions

### Python Code Style

- Use type hints where appropriate
- Prefer explicit over implicit
- Add docstrings for public functions
- Use existing utility functions from the codebase
- Follow PEP 8 conventions

### TypeScript/React Code Style

- Use functional components with hooks
- Follow existing component patterns
- Use proper TypeScript typing
- Keep components small and focused

## 7. Project-Specific Conventions

### Database Configuration

- Environment variables from `docker/.env` are used
- Service config in `docker/service_conf.yaml.template`
- Support for both Elasticsearch and Infinity (set `DOC_ENGINE=infinity`)

### API Patterns

- Flask blueprints in `api/apps/`
- Service layer in `api/db/services/`
- Request validation in API routes
- Use decorators for authentication (@login_required)

### Agent Components

- Located in `agent/`
- Component types: llm, retrieval, categorize, http, code, switch, etc.
- Use async/await for I/O operations

### Testing Patterns

- Use conftest.py for shared fixtures
- Mock external services where appropriate
- Use hypothesis_utils.py for property-based testing
- Test files mirror the source structure

## 8. Key Configuration Files

- `docker/.env` - Environment variables for Docker
- `docker/service_conf.yaml.template` - Backend service configuration
- `pyproject.toml` - Python dependencies (uses uv)
- `web/package.json` - Frontend dependencies and scripts

## 9. Environment Variables

### LOCAL_DEPLOYMENT

The `LOCAL_DEPLOYMENT` environment variable controls security-sensitive behaviors that are theoretically unsafe but practically acceptable in controlled environments.

**Values**: `true`, `1`, `yes` (case-insensitive) to enable; any other value disables.

**Default**: `false`

**Effects when enabled**:

- **Container reuse in sandbox**: The code execution sandbox will reuse containers instead of recreating them after each execution. This improves performance but means:
  - State persists between executions (files, environment variables)
  - Potentially malicious code could leave artifacts for subsequent executions
  - Only safe in trusted, isolated environments (e.g., local development, air-gapped deployments)

**When to enable**:
- Local development where all code is trusted
- Air-gapped/on-premise deployments with trusted users
- CI/CD pipelines with isolated execution environments

**When to disable (default)**:
- Production deployments with untrusted user code
- Multi-tenant environments
- Any scenario where code isolation between executions is critical

**Example**:
```bash
# Enable for local development
export LOCAL_DEPLOYMENT=true

# Or in docker/.env
LOCAL_DEPLOYMENT=true
```

## 10. Common Development Tasks

### Adding a New API Endpoint

1. Create/update blueprint in `api/apps/`
2. Add route handler with validation
3. Add service function in `api/db/services/`
4. Add tests in `test/testcases/test_web_api/`

### Adding a New Agent Component

1. Create component in `agent/` directory
2. Register component in the component registry
3. Add component configuration schema
4. Add tests in `test/unit_test/`

### Database Changes

1. Modify model in `api/db/db_models.py`
2. Add migration if needed (check existing migration patterns)
3. Update service layer in `api/db/services/`

## 11. Development Environment Requirements

- Python 3.10-3.12
- Node.js >=18.20.4
- Docker & Docker Compose >= v2.26.1
- uv package manager
- 16GB+ RAM, 50GB+ disk space
- gVisor (optional, for code executor/sandbox feature)