# RAGFlow Test Suite Audit (TODO_TESTS.md)

This document identifies critical gaps, excessive mocking, and reliability issues in the current RAGFlow test suite, categorized by project area.

---

## 🔴 CRITICAL GAPS & MISSING COVERAGE

### 1. End-to-End (E2E) Integration
- [x] Full RAG Pipeline - Covered
- [x] Multimodal Flow - Covered  
- [x] Parser Documents Coverage - Fixed

### 2. Agent & Workflow Logic
- [x] Branching Logic tests - Covered
- [x] Looping & Iteration tests - Covered
- [x] Race Conditions tests - Covered
- [x] State Persistence tests - Covered

### 3. GraphRAG & Entity Resolution
- [x] Entity Resolution tests - Covered
- [x] Graph Construction tests - Covered
- [x] OOM Protection tests - Covered

### 4. Database & Infrastructure
- [x] Migrations tests - Covered
- [x] Multi-Tenant Isolation tests - Covered
- [x] DB Service Mocking - Partial (SQLite migration in progress)

---

## 🟡 EXCESSIVE & BRITTLE MOCKING

### 5. RAG & LLM Abstractions
- [ ] **Deep-Mocking Routes**: Unit tests mock entire service layer hiding interaction bugs
  - Status: Cannot fix without architectural changes (see docs/TEST_MOCKING_PLAN.md)

### 6. Web API (`test/testcases/test_web_api/`)
- [ ] **Golden Samples**: README exists but no actual sample files in `test/samples/`
- [🟠 **HIGH**] Missing status code assertions in HTTP API tests (`test_http_api/common.py`)
- [🟡 **MEDIUM**] Hardcoded encrypted password in configs.py

---

## 🟠 HIGH PRIORITY TEST IMPROVEMENTS

### Test Isolation Issues
- [🟠 **HIGH**] `test/testcases/conftest.py:147-154` - set_tenant_info with autouse=True, scope="session" causes cross-test pollution
- [🟠 **HIGH**] `test/unit_test/agent/conftest.py:41-256` - _setup_mocks() runs at module import time, modifying sys.modules globally

### Missing Component Coverage
- [🟠 **HIGH**] No tests for agent components: Begin, LLM/Generate, Message, StringTransform, DataOperations, ListOperations, ExcelProcessor, Fillup, Invoke, VariableAssigner, VariableAggregator, ExitLoop, AgentWithTools, DocsGenerator
- [🟠 **HIGH**] No tests for agent tools: Google, Tavily, DuckDuckGo, SearXNG, Arxiv, PubMed, GitHub, Email, ExeSQL, DeepL, YahooFinance, etc.

### Missing Test Coverage
- [🟠 **HIGH**] No unit tests for rag/graphrag/entity_resolution.py
- [🟠 **HIGH**] No unit tests for api/db/services/tenant_llm_service.py, system_settings_service.py, pipeline_operation_log_service.py
- [🟠 **HIGH**] No tests for api/apps/plugin_app.py

---

## 🟡 MEDIUM PRIORITY TEST IMPROVEMENTS

### Weak Test Assertions
- [🟡 **MEDIUM**] `test/unit_test/rag/test_chunking_comprehensive.py:42` - `assert len(chunks) <= expected_count + 1` too permissive
- [🟡 **MEDIUM**] `test/unit_test/rag/test_task_executor.py` - Only static code analysis, no runtime testing

### Flaky Tests
- [🟡 **MEDIUM**] `test/unit_test/rag/test_retry_mechanism.py:204` - `assert wait1 != wait2 or True` always passes

### Duplicate Code
- [🟡 **MEDIUM**] Mock implementations duplicated across test_kb_app.py, test_document_app.py, test_user_app.py
- [🟡 **MEDIUM**] Duplicate conftest.py files in test/unit_test/rag/ (conftest.py and conftest_refactored.py)

### Test Data
- [🟡 **MEDIUM**] Golden sample test data directory doesn't exist for OCR tests
- [🟡 **MEDIUM**] No comprehensive PDF parser tests (only garbled detection exists)

### Playwright Tests
- [🟡 **MEDIUM**] Hardcoded timeouts in test files instead of using centralized _constants.py
- [🟡 **MEDIUM**] Cross-browser testing not configured
- [🟡 **MEDIUM**] Coverage gaps: No Knowledge Graph tests, bulk operations, user permissions, settings beyond model providers

---

## 📋 PLANNING DOCUMENTS

1. **docs/TEST_MOCKING_PLAN.md** - Mocking rework architecture and 9-week migration plan
2. **test/TEST_DATA_FACTORIES_PLAN.md** - Test data factories implementation plan

---

## 🟢 RECOMMENDED IMPROVEMENTS

### 8. Testing Standards
- [ ] **Test Data Factories**: Implement factory_boy pattern (see test/TEST_DATA_FACTORIES_PLAN.md)
- [x] Status code assertions - Implemented in web API, missing in HTTP API

(End of file - total 107 lines)