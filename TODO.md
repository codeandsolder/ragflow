# RAGFlow Code Review - TODO List

Generated from comprehensive code review of all major modules.

---

## Priority Legend
- 🔴 **CRITICAL**: Security vulnerability or data corruption risk
- 🟠 **HIGH**: Major bug or significant technical debt
- 🟡 **MEDIUM**: Performance issue or maintainability concern
- 🟢 **LOW**: Minor improvement or cleanup

---

## 1. api/ - Backend API Server (6.5/10)

### Security
- [🔴 **CRITICAL**] CORS allows `*` (any origin) - `apps/__init__.py:61`
  - Use environment-based allowed origins
- [🔴 **HIGH**] Password check with decrypted value comparison - `user_app.py:545`
  - Use hash comparison only
- [🟠 **MEDIUM**] API key in token_required not validated for None - `apps/__init__.py:261`
  - Add explicit None check
- [🟡 **MEDIUM**] Broad exception catching leaks info - `api_utils.py:138-153`
  - Use specific exception types

### Performance
- [🟠 **HIGH**] N+1 query pattern - `document_service.py:111-114`
  - Batch-fetch all metadata at once
- [🟡 **MEDIUM**] 20-item IN clause limit creates multiple queries - `common_service.py:381-394`
  - Use database-native batch methods
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

## 2. rag/ - Core RAG Logic (6.5/10)

### Architecture
- [🔴 **CRITICAL**] `do_handle_task` is 250+ lines - `task_executor.py:966-1211`
  - Split into handler classes using Strategy pattern
- [🔴 **CRITICAL**] `Dealer` class is 650+ lines - `search.py:38-686`
  - Extract: Searcher, Reranker, CitationInserter
- [🔴 **CRITICAL**] LLM provider code duplication (40+ classes) - `chat_model.py`
  - Use template method pattern for common code

### Performance
- [🟠 **HIGH**] `hybrid_similarity` creates sklearn model on every call - `query.py:159-167`
  - Cache the model instance
- [🟡 **MEDIUM**] Magic threshold `0.63` with no explanation - `search.py:232-241`
- [🟡 **MEDIUM**] Hardcoded fusion weights `0.05,0.95` - `search.py:141`

### Reliability
- [🔴 **CRITICAL**] Global semaphore `chat_limiter` - `graphrag/utils.py:40`
  - Move to service context
- [🔴 **CRITICAL**] Magic timeout `10000000000` (30 years!) - `graphrag/general/index.py:64`
- [🔴 **CRITICAL**] No circuit breaker pattern
  - Failures cascade across services
- [🟠 **HIGH**] `time.sleep()` blocks event loop - `chat_model.py:319`
  - Use `asyncio.sleep()` instead

### Configuration
- [🟡 **MEDIUM**] No config validation throughout
- [🟡 **MEDIUM**] Hardcoded 500 char truncation in rerank - `rerank_model.py:533-534`
- [🟡 **MEDIUM**] Returns placeholder `1024` tokens - `embedding_model.py:144`

---

## 3. deepdoc/ - Document Parsing & OCR (7.5/10)

### Critical Bugs
- [🔴 **CRITICAL**] Infinite retry loop (100k iterations) - `ocr.py:365-372, 474-481`
  - Cap at 3-5 retries with backoff
- [🔴 **CRITICAL**] Recursive call with zoom factor causing OOM - `pdf_parser.py:1695-1696`
  - Add max recursion depth and use iterative approach
- [🔴 **CRITICAL**] `loaded_models` dict never cleared - `ocr.py:36`
  - Memory grows indefinitely in long-running processes

### Memory
- [🔴 **CRITICAL**] No streaming for large documents - entire PDF loaded
  - Implement page-by-page processing
- [🔴 **CRITICAL**] Page images at full resolution `72*zoomin` DPI - `pdf_parser.py:1545`
  - Add memory monitoring and adaptive processing
- [🟠 **HIGH**] No explicit memory cleanup after processing each page

### Error Handling
- [🔴 **CRITICAL**] Bare `except Exception` suppresses all errors - `pdf_parser.py:1582-1583`
  - Add specific exception handling
- [🟠 **HIGH**] No PDF validation or file size limits
  - Malformed PDFs could cause indefinite blocking
- [🟠 **HIGH**] No timeouts on PDF/image operations

### Code Quality
- [🟠 **HIGH**] `construct_table()` is ~300 lines - `table_structure_recognizer.py:152-216`
  - Violates single responsibility principle
- [🟠 **HIGH**] Duplicate labels in `LayoutRecognizer4YOLOv10` - `layout_recognizer.py:164-175`
  - "Table caption" and "Figure caption" appear twice
- [🟡 **MEDIUM**] `blockType()` duplicated across 3 files - violates DRY
- [🟡 **MEDIUM**] Magic number `b["top"] >= btm - 3` tolerance - `table_structure_recognizer.py:182`

### Edge Cases
- [🟠 **HIGH**] Password-protected PDFs not handled
- [🟡 **MEDIUM**] Right-to-left languages not handled
- [🟡 **MEDIUM**] Vertical text incomplete support
- [🟡 **MEDIUM**] Nested tables basic only
- [🟡 **MEDIUM**] Footnotes/endnotes merged with body text

---

## 4. agent/ - Canvas Workflow Engine (6/10)

### Security
- [🔴 **CRITICAL**] SQL injection in `exesql.py` - tools/exesql.py:58-115
  - Only checks specific password values, doesn't sanitize
  - Multiple statements via `split(";")` not validated
- [🔴 **CRITICAL**] gVisor runtime not enforced - `sandbox/executor_manager/core/container.py:88`
  - Containers may run unsandboxed if gVisor not installed
- [🔴 **CRITICAL**] Tmpfs with exec permission - `container.py:93-95`
  - `exec` permission could allow privilege escalation

### Async/Await Bugs
- [🔴 **CRITICAL**] Nested `asyncio.run()` calls - `component/message.py:77-78`
  - Will fail in async context
- [🔴 **CRITICAL**] `await` in non-async function - `message.py:150-151`
  - Inside `_stream()` sync function
- [🔴 **CRITICAL**] Blocking `asyncio.run()` - `tools/base.py:54-55`
  - Creates new event loop in sync context

### Error Handling
- [🔴 **CRITICAL**] String error returns instead of exceptions - `variable_assigner.py:121-186`
  - `"ERROR:VARIABLE_NOT_LIST"` becomes variable value
- [🟠 **HIGH**] Thread limiter shared across instances - `component/base.py:349`
- [🟠 **HIGH**] Exception handler bypasses normal flow - `canvas.py:578-587`
  - Goto can skip components that should execute

### Code Quality
- [🟠 **HIGH**] O(n²) complexity in list comprehension - `canvas.py:634-648`
- [🟡 **MEDIUM**] Assert instead of proper error handling - `variable_assigner.py:48-49`
- [🟡 **MEDIUM**] Silent JSON validation failure - `component/base.py:215-217`
- [🟡 **MEDIUM**] No file size limits in file parsing - `canvas.py:754-772`

### Sandbox
- [🟠 **HIGH**] Weak URL validation regex - `providers/self_managed.py:307-309`
- [🟡 **MEDIUM**] Busy-wait polling in container allocation - `container.py:168-182`

---

## 5. web/ - React Frontend (7/10)

### Security
- [🔴 **CRITICAL**] `dangerouslySetInnerHTML` without DOMPurify - `delete-source-modal.tsx:27,34`
  - XSS vulnerability
- [🟡 **MEDIUM**] `(newConfig as any).skipToken` bypasses type safety - `next-request.ts:96-97`
- [🟡 **MEDIUM**] No CSRF token handling

### TypeScript
- [🔴 **CRITICAL**] 410+ `any` type usages across codebase
  - Replace with proper generics or `unknown`
- [🟠 **HIGH**] `data?: any` loses type safety - `chat.ts:101,140`
- [🟡 **MEDIUM**] `Service<T>` uses `any` extensively - `register-server.ts:10`

### Performance
- [🟠 **HIGH**] `gcTime: 0` disables garbage collection - `use-chat-request.ts:81`
  - Memory leak risk
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

## 6. docker/ - Docker Deployment (5/10)

### Security
- [🔴 **CRITICAL**] Hardcoded default passwords - `.env:42,52,111,138,146`
  - All identical: `infini_rag_flow`
  - Generate: `openssl rand -hex 32`
- [🔴 **CRITICAL**] Passwords in health check commands visible in process list
  - `docker-compose-base.yml:115,140`
- [🔴 **CRITICAL**] Exposed management ports (MySQL, Redis, MinIO)
  - Bind to `127.0.0.1` only
- [🟠 **HIGH**] MinIO credentials hardcoded in `infinity_conf.toml:42-43`
  - `minioadmin` / `minioadmin`

### Configuration
- [🔴 **CRITICAL**] No resource limits on RAGFlow services - `docker-compose.yml`
  - Add `mem_limit`, `cpu_shares`
- [🔴 **CRITICAL**] No health checks for RAGFlow services
  - Add health check endpoints
- [🟠 **HIGH**] Containers run as root by default
- [🟠 **HIGH**] `eval` usage in entrypoint.sh - `entrypoint.sh:161-172`

### Nginx
- [🟠 **HIGH**] Missing security headers
  - X-Frame-Options, X-Content-Type-Options, X-XSS-Protection
- [🟠 **HIGH**] No rate limiting configured
- [🟡 **MEDIUM**] Worker connections too low (1024)

### Container Hardening
- [🟡 **MEDIUM**] No read-only root filesystem
- [🟡 **MEDIUM**] No ulimits configured
- [🟡 **MEDIUM**] Sandbox executor uses `privileged: true` - `docker-compose-base.yml:148-174`

---

## 7. sdk/ - Python SDK (5/10)

### Error Handling
- [🔴 **CRITICAL**] No retry logic anywhere in the SDK
  - Network failures propagate unhandled
- [🔴 **CRITICAL**] Generic `Exception` only - no custom exception hierarchy
  - Callers can't distinguish error types
- [🔴 **CRITICAL**] No HTTP status code validation
  - Returns even on 500 errors

### Resource Management
- [🔴 **CRITICAL**] No context manager support (`__enter__`/`__exit__`)
  - Response objects may leak connections
- [🔴 **CRITICAL**] `requests.Session` not used
  - Each call creates new connection
- [🟠 **HIGH**] Streaming responses not explicitly closed - `session.py:47-73`

### Type Safety
- [🔴 **CRITICAL**] No type hints except few parameters
  - `beartype_this_package()` called but no hints exist
- [🟠 **HIGH**] Mutable default arguments - `chat.py:47`, `session.py:25`, `document.py:90`
  - Use `None` + initialization pattern

### API Design
- [🟠 **HIGH**] Inconsistent return types across list methods
  - `list_datasets` returns `list[DataSet]`, `list_memory` returns `dict`
- [🟠 **HIGH**] `update()` returns `self` in some modules, `None` in others
- [🟡 **MEDIUM**] `DataSet` vs `Agent` naming inconsistency
- [🟡 **MEDIUM**] `add_message` takes `memory_id: list[str]` but API likely expects single ID

### Documentation
- [🟠 **HIGH**] Minimal docstrings except one parameter
- [🟠 **HIGH**] `hello_ragflow.py` only prints version, no real usage
- [🟡 **MEDIUM**] No README.md in SDK directory

---

## 8. test/ - Testing Infrastructure (6.5/10)

### Test Quality
- [🔴 **CRITICAL**] 25+ tests marked `@pytest.mark.skip(reason="Failed")`
  - Features not implemented but tests exist
  - Fix or remove
- [🟠 **HIGH**] Commented cleanup code in `test_web_api/conftest.py:149-154`
  - Uncomment or remove
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

## Quick Wins (High Impact, Low Effort)

1. Generate random passwords in `.env`:
   ```bash
   openssl rand -hex 32
   ```

2. Add DOMPurify to `dangerouslySetInnerHTML` in `web/`

3. Fix infinite retry loops in `deepdoc/vision/ocr.py`:
   ```python
   # Change from 100000 to 3-5
   for i in range(5):
   ```

4. Remove dead code in `api/apps/kb_app.py:49-324`

5. Add resource limits to RAGFlow services in `docker-compose.yml`

6. Implement `__enter__`/`__exit__` on `RAGFlow` client class

7. Fix nested `asyncio.run()` calls in `agent/component/message.py`

8. Create custom exception hierarchy in `sdk/ragflow_sdk/`

---

## Long-term Improvements

1. **Refactor large classes**:
   - `Dealer` (650 lines) → Searcher, Reranker, CitationInserter
   - `do_handle_task` (250 lines) → Task handlers
   - `Canvas` store (659 lines) → Multiple stores

2. **Add circuit breakers** for external API calls

3. **Implement streaming** for large document processing

4. **Add comprehensive type hints** and enable strict TypeScript

5. **Create test data factories** for consistent test data

6. **Implement memory monitoring** and adaptive processing

7. **Add OpenAPI documentation** using existing QuartSchema

8. **Create baseline metrics** for benchmarking regressions
