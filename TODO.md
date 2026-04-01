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
- [🟠 **HIGH**] N+1 query patterns - Multiple locations:
  - `dialog_app.py:163-171` - get_kb_names() loops calling get_by_id()
  - `dialog_app.py:180-181` - list_dialogs() calls get_kb_names() per conversation
  - `kb_app.py:92-96` - list_tags() loops through tenants
- [🟡 **MEDIUM**] Missing pagination limits in list endpoints

### Security
- [🔴 **CRITICAL**] `user_app.py:437` - GitHub API token exposed in URL query string
- [🔴 **CRITICAL**] `user_app.py:256,269` - Open redirect via redirect(f"/?error={str(e)}")
- [🟠 **HIGH**] `document_app.py:824-827` - Path traversal risk with image_id.split("-")
- [🟠 **HIGH**] Missing `@resource_owner_required` in `chunk_app.py:503`

### Code Quality
- [🟡 **MEDIUM**] Inconsistent error handling - Uses `raise LookupError()` instead of error response
- [🟡 **MEDIUM**] `kb_app.py:402` - Passes string to server_error_response() instead of Exception
- [🟡 **MEDIUM**] Direct `request.args["..."]` access without validation (KeyError risk)

### REST Conventions
- [🟡 **MEDIUM**] POST used for read operations: `/filter`, `/completion`, `/ask`, `/next`, `/list`

---

## 2. rag/ - Core RAG Logic

### Code Quality
- [🟡 **MEDIUM**] Hardcoded magic numbers:
  - `search.py:35-42` - CITATION_SIMILARITY_THRESHOLD=0.63, MIN_THRESHOLD=0.3, DECAY=0.8
  - `search.py:571` - bs=128 batch size
  - `search.py:654,708` - vector_size=1024 hardcoded
  - `query.py:44` - min_match=0.6 hardcoded
- [🟡 **MEDIUM**] Unused parameters in search.py:587,593 ('S' parameter)
- [🟡 **MEDIUM**] Code duplication in tag_content()/tag_query():607,622

### Configuration
- [🟡 **MEDIUM**] No bounds validation for similarity_threshold, vector_similarity_weight

### Type Hints
- [🟡 **MEDIUM**] Missing type hints throughout rag/nlp/

---

## 3. deepdoc/ - Document Parsing & OCR

### Memory Issues
- [🟠 **HIGH**] `figure_parser.py:198` - Global ThreadPoolExecutor never shut down
- [🟠 **HIGH**] `pdf_parser.py:2380-2386` - pdfplumber not closed on exception

### Validation
- [🟡 **MEDIUM**] No file size validation in txt_parser, html_parser, docx_parser, ppt_parser, epub_parser

### Error Handling
- [🟡 **MEDIUM**] `pdf_parser.py:1803-1804` - Generic `except Exception` swallows errors
- [🟡 **MEDIUM**] `docx_parser.py:46-70` - Bare except hides issues

### Timeouts
- [🟡 **MEDIUM**] `pdf_parser.py:2388-2420` - No timeout on VisionParser vision model calls
- [🟡 **MEDIUM**] `figure_parser.py:282-288` - Future results without timeout

---

## 4. agent/ - Canvas Workflow Engine

### Silent Failures
- [🟠 **HIGH**] `component/message.py:197-198` - Silent exception swallowing with `except Exception: pass`

### Large Classes
- [🟡 **MEDIUM**] `canvas.py` 896 lines, `component/docs_generator.py` 1514 lines
- [🟡 **MEDIUM**] `component/message.py` 440 lines, `component/llm.py` 443 lines

### Security
- [🟡 **MEDIUM**] `sandbox/executor_manager/services/security.py:172-173` - Node.js security "defaulted to SAFE"
- [🟡 **MEDIUM**] `sandbox/executor_manager/services/security.py:167` - Dangerous code logged but not blocked

### Debug Code
- [🟡 **MEDIUM**] `canvas.py:350` - Debug print statement in production code

---

## 5. web/ - React Frontend

### Console Statements
- [🟡 **MEDIUM**] 100+ console.log/debug statements in production code

### Accessibility
- [🟡 **MEDIUM**] Deprecated onKeyPress usage - should use onKeyDown/onKeyUp
- [🟡 **MEDIUM**] Missing keyboard handlers on clickable divs
- [🟡 **MEDIUM**] Missing aria-labels on icon-only buttons (100+ occurrences)
- [🟡 **MEDIUM**] Empty alt attributes on images

### TypeScript
- [🟡 **MEDIUM**] Excessive 'any' usage (828+ instances)
- [🟡 **MEDIUM**] UseRef<any> types should be specific

### Large Components
- [🟡 **MEDIUM**] admin/users.tsx 812 lines, admin/sandbox-settings.tsx 577 lines

### Memory Leaks
- [🟡 **MEDIUM**] use-chat.ts:77-85 - resetAnswer timer not cleared on unmount

---

## 6. sdk/ - Python SDK

### Documentation
- [🟡 **MEDIUM**] Missing docstrings: session.py methods, dataset.py update_auto_metadata()
- [🟡 **MEDIUM**] modules/__init__.py - Empty file, no documentation

### Type Hints
- [🟡 **MEDIUM**] Missing type hints in session.py, dataset.py, memory.py multiple methods

### Error Handling
- [🟡 **MEDIUM**] session.py:50-97 - ask() lacks exception handling for stream failures
- [🟡 **MEDIUM**] dataset.py:255-261 - parse_documents() swallows potential errors

---

## 7. docker/ - Docker Deployment

### Missing Health Checks
- [🟡 **MEDIUM**] tei-cpu, tei-gpu no healthcheck defined
- [🟡 **MEDIUM**] ragflow-cpu, ragflow-gpu no healthcheck

### Resource Limits
- [🟡 **MEDIUM**] tei-cpu, tei-gpu no deploy.resources.limits
- [🟡 **MEDIUM**] ragflow services missing CPU/memory limits

### Security
- [🟡 **MEDIUM**] .env:304 - Hardcoded default LITELLM_MASTER_KEY

---

## 8. rag/llm/ - LLM Models

### Missing Retry Logic
- [🟠 **HIGH**] 15+ encode() methods lack retry despite Base inheritance

### Error Handling
- [🟠 **HIGH**] Multiple encode() methods have no try/catch or status checking

### Type Hints
- [🟡 **MEDIUM**] Missing type hints on encode(), encode_queries() throughout

### Code Duplication
- [🟡 **MEDIUM**] Highly similar encode() patterns across OpenAIEmbed, LocalAIEmbed, etc.

---

## 9. rag/graphrag/ - GraphRAG

### Error Handling
- [🟠 **HIGH**] `utils.py:236` - Potential KeyError in graph_merge without existence check

### Test Coverage
- [🟠 **HIGH**] No unit tests for entity_resolution.py
- [🟡 **MEDIUM**] No integration tests for graph extraction pipeline

### Debug Code
- [🟡 **MEDIUM**] `general/index.py:178-189` - Hardcoded "FIX" comments and debug strings

### Resource Leaks
- [🟡 **MEDIUM**] `general/graph_extractor.py:80-86` - tiktoken encoding never closed

---

## 10. test/ - Testing Infrastructure

### Test Isolation
- [🟡 **MEDIUM**] configs.py:27 - Comment reveals plaintext password "123"

### Over-mocking
- [🟠 **HIGH**] test/unit_test/api/tests mock entire services hiding interaction bugs

### Weak Assertions
- [🟡 **MEDIUM**] test/unit_test/rag/ - Weak assertions like `assert len(chunks) <= expected_count + 1`

### Flaky Tests
- [🟡 **MEDIUM**] test_retry_mechanism.py:204 - `assert wait1 != wait2 or True` always passes

### Missing Coverage
- [🟠 **HIGH**] No tests for agent component: Begin, LLM, Message, DataOperations, etc.
- [🟠 **HIGH**] No tests for agent tools: Google, Tavily, DuckDuckGo, etc.

---

## 11. web/hooks and stores

### Type Safety
- [🟡 **MEDIUM**] web/src/hooks/use-chat.ts:64 - UseRef<any> should be specific
- [🟡 **MEDIUM**] web/src/hooks/common-hooks.tsx:84 - any type in callbacks

### Memory Leaks
- [🟡 **MEDIUM**] use-chat.ts:77-85 - timer not cleared

### Large Files
- [🟡 **MEDIUM**] use-chat.ts 527 lines, use-chat-request.ts 554 lines

---

## Planning Documents Created

1. `docs/TEST_MOCKING_PLAN.md` - Mocking rework architecture and migration plan
2. `test/TEST_DATA_FACTORIES_PLAN.md` - Test data factories implementation plan

---

## Long-term Improvements

1. **OpenAPI documentation**: Add route decorators to generate OpenAPI docs

2. **Test data factories**: Implement factory_boy pattern

3. **Mocking rework**: Follow TEST_MOCKING_PLAN.md

4. **Reduce console.log**: Replace with proper logging throughout web/

5. **TypeScript strictness**: Replace 'any' types with proper types

(End of file - total 214 lines)