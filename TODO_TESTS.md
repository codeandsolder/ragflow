# RAGFlow Test Suite Audit (TODO_TESTS.md)

This document identifies critical gaps, excessive mocking, and reliability issues in the current RAGFlow test suite, categorized by project area.

---

## 🔴 CRITICAL GAPS & MISSING COVERAGE

### 1. End-to-End (E2E) Integration
- [ ] **Full RAG Pipeline**: No single test covers the complete flow: **Create KB -> Upload Doc -> Wait for Parse -> Create Dialog -> Chat**.
- [ ] **Multimodal Flow**: Missing integration tests for image-to-chat and table-to-chat workflows.
- [ ] **Paser Documents Coverage**: `test_paser_documents.py` (which contains a typo in its name) only verifies the "Task done" state for parsing but does not verify that the resulting chunks are searchable or chat-capable.

### 2. Agent & Workflow Logic (`test/unit_test/agent/`)
- [ ] **Branching Logic**: No unit tests for `Switch`, `Categorize`, or complex `DSL` parsing.
- [ ] **Looping & Iteration**: `LoopItem` and `Iteration` components are entirely untested.
- [ ] **Race Conditions**: No tests verify thread safety when multiple agents access `Canvas.globals` concurrently.
- [ ] **State Persistence**: No tests verify if state correctly persists (or is cleared) across turns when `LOCAL_DEPLOYMENT` (container reuse) is toggled.

### 3. GraphRAG & Entity Resolution (`test/unit_test/rag/`)
- [ ] **Entity Resolution**: **Zero coverage** for `entity_resolution.py`. No verification that "IBM" and "International Business Machines" are correctly merged.
- [ ] **Graph Construction**: No tests for the end-to-end extraction pipeline (Chunk -> Graph).
- [ ] **OOM Protection**: No tests for graph size limits or memory-efficient loading.

### 4. Database & Infrastructure (`test/unit_test/api/`)
- [ ] **Migrations**: No tests verify schema upgrades in `migrate_db()`.
- [ ] **Multi-Tenant Isolation**: No tests verify that User A's execution in the sandbox cannot see User B's files/env-vars.
- [ ] **DB Service Mocking**: Over-reliance on mocking ORM internals (`_FakeQuery`, `_FieldStub`) in `test/unit_test/api/db/services/`.

---

## 🟡 EXCESSIVE & BRITTLE MOCKING

### 5. RAG & LLM Abstractions
- [ ] **`conftest.py` Over-Mocking**: Global `sys.modules` stubbing for `tiktoken`, `openai`, etc., prevents testing real tokenization or truncation logic.
- [ ] **Retry & Fallback**: No tests verify that `RemoteModelBase` actually retries on 429 errors or fails over to secondary providers.

### 6. Web API (`test/testcases/test_web_api/`)
- [ ] **Deep-Mocking Routes**: Unit tests (e.g., `test_conversation_routes_unit.py`) mock the entire service layer, hiding interaction bugs.
- [ ] **Status Code Neglect**: Helpers in `common.py` ignore `res.status_code`, potentially hiding 500 errors if the body contains a "code" field.

### 7. DeepDoc & Vision (`test/unit_test/deepdoc/`)
- [ ] **Logic-Only OCR Tests**: `test_ocr.py` uses coordinate-sorting mocks instead of "golden sample" images. It cannot detect regressions in actual model accuracy.
- [ ] **Missing Parser Coverage**: Core parsers like `DocxParser`, `ExcelParser`, and `PPTParser` lack dedicated unit tests.

---

## 🟢 RECOMMENDED IMPROVEMENTS

### 8. Testing Standards
- [ ] **Transition to SQLite**: Replace `_FakeQuery` and `_FieldStub` mocks with an in-memory SQLite database for service-layer tests.
- [ ] **Standardize Status Assertions**: Update all API tests to explicitly assert `res.status_code == 200`.
- [ ] **Golden Samples**: Store a small set of "golden" PDF/Image samples in `test/samples/` for vision and parser integration tests.
- [ ] **Parameterize Edge Cases**: Add tests for empty documents, whitespace-only chunks, and extreme UTF-8 characters.
