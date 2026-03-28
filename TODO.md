# RAGFlow Code Review - TODO List

Generated from comprehensive code review of all major modules.

---

## Priority Legend
- 🔴 **CRITICAL**: Security vulnerability or data corruption risk
- 🟠 **HIGH**: Major bug or significant technical debt
- 🟡 **MEDIUM**: Performance issue or maintainability concern
- 🟢 **LOW**: Minor improvement or cleanup

---

## 1. api/ - Backend API Server

### Performance
- [🟠 **HIGH**] N+1 query pattern - `document_service.py:111-114`
- Batch-fetch all metadata at once
- [🟡 **MEDIUM**] No pagination limits - `document_service.py:173-174`
- Add default limits to prevent memory exhaustion

### Code Quality
- [🔴 **CRITICAL**] Extensive dead code (275+ lines commented) - `kb_app.py:49-324`
- Remove or properly deprecate
- [🟠 **HIGH**] OAuth callback duplication - `user_app.py:272-461`
- Extract common handler logic
- [🟠 **HIGH**] Inconsistent response formats - `api_utils.py`
- Consolidate to single pattern: `{"code", "message", "data"}`
- [🟡 **MEDIUM**] Weak input validation - `api_utils.py:156-203`
- Add type, length, and sanitization validation
- [🟡 **MEDIUM**] REST convention violations - `document_app.py`
- Use GET for list/infos, POST only for mutations

### Testing
- [🔴 **CRITICAL**] No test infrastructure in api/
- Add pytest configuration and mock fixtures

---

## 2. rag/ - Core RAG Logic

### Architecture
- [🔴 **CRITICAL**] `do_handle_task` is 246 lines - `task_executor.py:966-1211`
- Split into handler classes using Strategy pattern
- [🔴 **CRITICAL**] LLM provider code duplication (40+ classes) - `chat_model.py`
- Use template method pattern for common code

### Performance
- [🟠 **HIGH**] `hybrid_similarity` creates sklearn model on every call - `query.py:159-167`
- Cache the model instance
- [🟡 **MEDIUM**] Magic threshold `0.63` with no explanation - `search.py:232-241`
- [🟡 **MEDIUM**] Hardcoded fusion weights `0.05,0.95` - `search.py:141`

### Configuration
- [🟡 **MEDIUM**] No config validation throughout

---

## 3. deepdoc/ - Document Parsing & OCR

### Critical Bugs
- [🔴 **CRITICAL**] No streaming for large documents - entire PDF loaded
- Implement page-by-page processing
- [🔴 **CRITICAL**] Page images at full resolution `72*zoomin` DPI - `pdf_parser.py:1545`
- Add memory monitoring and adaptive processing
- [🟠 **HIGH**] No explicit memory cleanup after processing each page

### Error Handling
- [🟠 **HIGH**] No PDF validation or file size limits
- Malformed PDFs could cause indefinite blocking
- [🟠 **HIGH**] No timeouts on PDF/image operations

### Edge Cases
- [🟠 **HIGH**] Password-protected PDFs not handled
- [🟡 **MEDIUM**] Right-to-left languages not handled
- [🟡 **MEDIUM**] Vertical text incomplete support
- [🟡 **MEDIUM**] Nested tables basic only
- [🟡 **MEDIUM**] Footnotes/endnotes merged with body text

---

## 4. agent/ - Canvas Workflow Engine

### Code Quality
- [🟡 **MEDIUM**] Silent JSON validation failure - `component/base.py:215-217`

### Sandbox
- [🟡 **MEDIUM**] Sandbox executor uses `privileged: true` - `docker-compose-base.yml:148-174`

---

## 5. web/ - React Frontend

### Performance
- [🟡 **MEDIUM**] Large Zustand store (659 lines) - `agent/store.ts:122-656`
- [🟡 **MEDIUM**] Large `useSelectDerivedMessages` hook (200 lines) - `logic-hooks.ts:447-644`
- [🟡 **MEDIUM**] No `React.memo()` on list item components

### Code Quality
- [🟠 **HIGH**] Redundant auth cleanup calls - `request.ts:165-166`
- [🟡 **MEDIUM**] `console.log` instead of proper error logging - `next-request.ts:149`
- [🟡 **MEDIUM**] `eslint-disable-next-line eqeqeq` needs justification - `agent/store.ts:575`

### Accessibility
- [🟠 **HIGH**] Limited `aria-*` attributes
- [🟡 **MEDIUM**] No skip links for keyboard navigation
- [🟡 **MEDIUM**] Missing focus management in modals

---

## 6. docker/ - Docker Deployment

### Container Hardening
- [🟡 **MEDIUM**] Sandbox executor uses `privileged: true` - `docker-compose-base.yml:148-174`

---

## 7. sdk/ - Python SDK

### Documentation
- [🟠 **HIGH**] Minimal docstrings except one parameter
- [🟠 **HIGH**] `hello_ragflow.py` only prints version, no real usage
- [🟡 **MEDIUM**] No README.md in SDK directory

---

## 8. test/ - Testing Infrastructure

### Test Quality
- [🟡 **MEDIUM**] Some test files too large (>300 lines)

### Coverage Gaps
- [🟠 **HIGH**] No unit tests for `api/apps/` endpoints
- [🟠 **HIGH**] No tests for `rag/llm/` (only 1 test file)
- [🟠 **HIGH**] No tests for `rag/nlp/`, `agent/tool/`, `deepdoc/ocr/`, `rag/svr/`
- [🟡 **MEDIUM**] No E2E tests for agent workflow builder

### E2E Reliability
- [🟠 **HIGH**] No retry mechanisms for flaky tests
- [🟡 **MEDIUM**] Hardcoded timeouts (`RESULT_TIMEOUT_MS = 15000`)
- [🟡 **MEDIUM**] Hardcoded model names: `"glm-4-flash@ZHIPU-AI"`

### Test Data
- [🟠 **HIGH**] No test data factories (like Factory Boy)
- [🟡 **MEDIUM**] Creates files on-the-fly, no fixtures
- [🟡 **MEDIUM**] Hardcoded credentials: `"qa@infiniflow.org"`, `"123"`

### Benchmarking
- [🟡 **MEDIUM**] No baseline comparison for regressions
- [🟡 **MEDIUM**] Limited metrics (only latency, no throughput)
- [🟡 **MEDIUM**] No trend visualization or alerting

---

## Long-term Improvements

1. **Refactor large classes**:
- `Dealer` (334 lines) → Searcher, Reranker, CitationInserter
- `do_handle_task` (246 lines) → Task handlers
- `Canvas` store (659 lines) → Multiple stores

2. **Implement streaming** for large document processing

3. **Add comprehensive type hints** and enable strict TypeScript

4. **Create test data factories** for consistent test data

5. **Implement memory monitoring** and adaptive processing

6. **Add OpenAPI documentation** using existing QuartSchema

7. **Create baseline metrics** for benchmarking regressions
