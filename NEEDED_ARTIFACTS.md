---

## Agent 9: Agent State Persistence Test Specialist
**Task**: Create tests verifying state persistence behavior with LOCAL_DEPLOYMENT toggle (container reuse)
**Source File(s)**:
- `agent/sandbox/executor_manager/core/container.py` - Container lifecycle management
- `agent/sandbox/executor_manager/util.py` - Environment variable parsing
- `agent/sandbox/executor_manager/services/execution.py` - Code execution service
- `AGENTS.md` - LOCAL_DEPLOYMENT documentation
**Needed Artifacts**:
- [x] `test/unit_test/agent/test_state_persistence.py` - Created comprehensive test file with:
  - `TestStatePersistence` class with 6 test methods covering:
    - `test_state_cleared_without_local_deployment` - Verifies containers recreated when LOCAL_DEPLOYMENT=false
    - `test_state_persists_with_local_deployment` - Verifies containers reused when LOCAL_DEPLOYMENT=true
    - `test_file_persistence_across_executions` - Verifies files persist in reused containers
    - `test_env_var_isolation` - Verifies environment variables persist across executions
    - `test_process_cleanup_verification` - Verifies process cleanup via container recreation
    - `test_memory_cleanup_between_runs` - Verifies no memory cleanup in LOCAL_DEPLOYMENT mode
  - `TestLocalDeploymentEnvParsing` - Parametrized tests for env var parsing
  - `TestContainerReuseSecurity` - Security implication tests
**Priority**: High
**Notes**: 
- Tests use mocking to avoid actual Docker container operations
- All tests verify behavior documented in AGENTS.md regarding LOCAL_DEPLOYMENT toggle
- Security implications: container reuse allows state persistence (files, env vars, memory)

---

## Agent 22: Golden Samples Directory Setup Specialist
**Task**: Establish test/samples/ directory structure and documentation
**Source File(s)**: N/A - infrastructure setup
**Needed Artifacts**:
- [ ] `test/samples/documents/pdf/sample_simple.pdf` - Simple PDF with plain text paragraphs
- [ ] `test/samples/documents/pdf/sample_with_images.pdf` - PDF containing embedded images
- [ ] `test/samples/documents/pdf/sample_with_tables.pdf` - PDF with table structures
- [ ] `test/samples/documents/pdf/sample_multilingual.pdf` - PDF with multiple languages (EN, ZH, JA)
- [ ] `test/samples/documents/docx/sample_simple.docx` - Simple Word document
- [ ] `test/samples/documents/docx/sample_with_tables.docx` - Word document with tables
- [ ] `test/samples/documents/xlsx/sample_simple.xlsx` - Simple Excel spreadsheet
- [ ] `test/samples/documents/xlsx/sample_with_formulas.xlsx` - Excel with formulas
- [ ] `test/samples/documents/pptx/sample_simple.pptx` - Simple PowerPoint presentation
- [ ] `test/samples/images/sample_text.png` - Image containing text
- [ ] `test/samples/images/sample_table.png` - Image containing table data
- [ ] `test/samples/images/sample_chart.png` - Image containing chart/graph
- [ ] `test/samples/expected_outputs/pdf_simple.json` - Expected extraction JSON
- [ ] `test/samples/expected_outputs/pdf_with_tables.json` - Expected table extraction JSON
- [ ] `test/samples/expected_outputs/docx_simple.json` - Expected docx extraction JSON
- [ ] `test/samples/expected_outputs/xlsx_simple.json` - Expected xlsx extraction JSON
- [ ] `test/samples/expected_outputs/image_text.json` - Expected OCR JSON
**Priority**: Medium
**Notes**: These are golden sample files for testing document parsing, OCR, and extraction functionality. Samples should be synthetic/generated for testing, not sourced from external copyrighted materials.

---

## TEST REVIEW FINDINGS (March 2026)

This section documents the review findings from 15 parallel test reviewers.

### HIGH PRIORITY FIXES NEEDED

| Test File | Issue | Fix Required |
|-----------|-------|--------------|
| `test_e2e_rag_pipeline.py` | `create_txt_file` signature mismatch - custom content ignored | Fix file creation to use actual custom content or remove content parameter |
| `test_e2e_rag_pipeline.py` | `pytest.request.addfinalizer` should be `request.addfinalizer` | Fix fixture parameter reference |
| `test_e2e_multimodal.py` | Missing import for `create_txt_file` at line 199 | Add import statement |
| `test_state_persistence.py` | Test logic flawed - doesn't actually test file/env var persistence | Rewrite to actually verify file/env var persistence |
| `test_state_persistence.py` | Missing "on" value in env parsing test | Add "on" to parametrized values |
| `test_migrations.py` | Mocking approach flawed - patches after import | Fix mocking to patch before import or use different approach |
| `test_migrations.py` | Silent exception handling | Remove try/except with pass |
| `test_sqlite_services.py` | SQLite models missing BaseModel fields (create_time, update_time) | Add timestamp fields to match real models |
| `test_sqlite_services.py` | Missing JSONField equivalent for parser_config | Add JSON serialization testing |
| `test_edge_case_documents.py` | Constructor argument issue - uses string "File" as ID | Fix to use proper ID or document pattern |
| `test_edge_case_documents.py` | Null byte test uses escaped string, not actual null bytes | Fix to use actual null bytes |
| `test_dsl_parsing.py` | Missing branching flow tests (categorize/switch) | Add branching DSL tests |
| `test_dsl_parsing.py` | Missing parallel execution tests | Add parallel component tests |
| `test_dsl_parsing.py` | Missing loop/iteration component tests | Add iteration component tests |
| `test_retry_mechanism.py` | Missing backoff timing verification | Add actual timing tests |
| `test_retry_mechanism.py` | Missing circuit breaker state transition tests | Add open/closed/recovery tests |
| `test_memory_management.py` | Tests use mock functions, not actual implementation | Import and test actual GraphMemoryMonitor functions |
| `test_memory_management.py` | Potential infinite loop in progressive loading test | Add max iteration limit |

### MEDIUM PRIORITY IMPROVEMENTS

| Test File | Missing Coverage |
|-----------|------------------|
| `test_e2e_rag_pipeline.py` | Streaming chat, multi-turn conversations, error handling |
| `test_e2e_multimodal.py` | Corrupted files, empty docs, network failures, content validation |
| `test_switch.py` | Integration tests for ≠, ≥, ≤ operators, whitespace input edge cases |
| `test_graph_construction.py` | Self-referential edges, disconnected components |
| `test_migrations.py` | update_tenant_llm_to_id_primary_key tests, more idempotency |
| `test_parser_tests/` | Corrupted file handling, password-protected files |

### COMPLETE & PRODUCTION READY

These tests are thorough and well-structured:
- ✅ `test_graph_construction.py` (95% complete, A+ rating)
- ✅ `common.py` status code helpers (comprehensive, backward compatible)
- ✅ `test_docx_parser.py`, `test_excel_parser.py`, `test_ppt_parser.py` (95% complete)
- ✅ `test/utils/` utilities (90% complete, comprehensive)
- ✅ `test_samples/README.md` (well-documented structure)

### FILES THAT NEED ACTUAL SAMPLE CREATION

The following sample files are documented but NOT YET CREATED:
- All files in `test/samples/documents/` (PDF, DOCX, XLSX, PPTX)
- All files in `test/samples/images/`
- All files in `test/samples/expected_outputs/`

---

---

## Agent 12: GraphRAG OOM Protection Test Specialist
**Task**: Create tests for graph size limits and memory-efficient loading
**Source File(s)**: `rag/graphrag/utils.py`, `rag/graphrag/general/index.py`
**Needed Artifacts**:
- [ ] `test/unit_test/rag/graphrag/fixtures/large_graph_1000_nodes.json` - Graph fixture with 1000 nodes and ~5000 edges for stress testing
- [ ] `test/unit_test/rag/graphrag/fixtures/large_graph_5000_nodes.json` - Graph fixture with 5000 nodes for OOM simulation
- [ ] `test/unit_test/rag/graphrag/fixtures/chunked_graphs/` - Directory containing pre-chunked subgraphs for memory-efficient loading tests
- [ ] `test/unit_test/rag/graphrag/fixtures/config_max_nodes_1000.json` - Configuration fixture with max_nodes=1000 limit
- [ ] `test/unit_test/rag/graphrag/fixtures/config_max_memory_512mb.json` - Configuration fixture with max_memory=512MB limit
- [ ] `test/unit_test/rag/graphrag/mock_memory_profiler.py` - Mock memory profiling utility for tracking memory usage in tests
- [ ] `test/unit_test/rag/graphrag/fixtures/edge_cases/empty_graph.json` - Empty graph fixture
- [ ] `test/unit_test/rag/graphrag/fixtures/edge_cases/single_node_graph.json` - Single node graph fixture
- [ ] `test/unit_test/rag/graphrag/fixtures/edge_cases/dense_graph.json` - Fully connected dense graph for stress testing
**Priority**: High
**Notes**: These artifacts support testing memory management, graph size limits, chunking, and OOM handling in the GraphRAG module. Fixtures should include realistic graph structures with proper node/edge attributes matching the nx.Graph node_link_data format.
**Task**: Create tests for the end-to-end graph extraction pipeline (Chunk -> Graph)
**Source File(s)**:
- `rag/graphrag/general/extractor.py` - Core extraction logic
- `rag/graphrag/general/graph_extractor.py` - Graph extraction implementation
- `rag/graphrag/general/index.py` - GraphRAG pipeline orchestration

### Sample Document Chunks with Known Entities/Relations

#### Simple Chunk (English)
```text
Alice works at Google. She develops machine learning algorithms.
```
**Expected Entities**:
- Alice (person) - "Works at Google, develops ML algorithms"
- Google (organization) - "Technology company"
- Machine Learning (category) - "ML algorithms"

**Expected Relations**:
- Alice -> Google (employment, weight: 8)
- Alice -> Machine Learning (develops, weight: 7)

#### Multi-Chunk Document
**Chunk 1**: "Alice works at Google. She develops machine learning algorithms."
**Chunk 2**: "Bob is a researcher at MIT. He collaborates with Alice on AI projects."

**Expected Merged Entities**:
- Alice (person) - Combined description from both chunks
- Google (organization) - From chunk 1
- Bob (person) - From chunk 2
- MIT (organization) - From chunk 2
- AI (category) - From chunk 2

**Expected Merged Relations**:
- Alice -> Google (works at)
- Bob -> MIT (affiliated with)
- Alice -> Bob (collaborates on AI)

#### Multilingual Chunk
```text
张三是一名工程师，在北京工作。Tokyo is the capital of Japan.
```
**Expected Entities**:
- 张三 (person) - Chinese name
- 北京 (geo) - Beijing, China
- Tokyo (geo) - Capital of Japan
- Japan (geo) - Country

**Expected Cross-language Relations**:
- 张三 -> Beijing (works in)
- Tokyo -> Japan (capital of)

### Mock LLM Responses for Extraction

#### Simple Extraction Response
```
("entity"<|>Alice<|>person<|>Alice works at Google and develops ML algorithms)<|>
("entity"<|>Google<|>organization<|>Google is a technology company)<|>
("entity"<|>Machine Learning<|>category<|>ML algorithms developed by Alice)<|>
("relationship"<|>Alice<|>Google<|>Alice works at Google<|>employment<|>8)<|>
("relationship"<|>Alice<|>Machine Learning<|>Alice develops ML algorithms<|>develops<|>7)<|>
<|COMPLETE|>
```

#### Multi-Entity Response (with gleaning)
Initial extraction:
```
("entity"<|>Alice<|>person<|>Alice works at Google")
```
Continue prompt adds:
```
("entity"<|>Machine Learning<|>category<|>Algorithms developed by Alice")
```

### Expected Graph Structures

#### Single Chunk Graph (NetworkX)
```python
{
    nodes: {
        "ALICE": {"entity_type": "PERSON", "description": "...", "source_id": ["chunk_0"]},
        "GOOGLE": {"entity_type": "ORGANIZATION", "description": "...", "source_id": ["chunk_0"]},
    },
    edges: [
        ("ALICE", "GOOGLE", {"description": "...", "weight": 8.0, "keywords": ["employment"]})
    ]
}
```

#### Merged Graph (after multiple chunks)
- Nodes merged by name (case-insensitive)
- Descriptions concatenated with `<SEP>` separator
- source_id lists merged (unique values)
- Edge weights aggregated
- Edge descriptions concatenated

### Test Data Artifacts

#### Unit Test Fixtures
- [ ] `test/samples/graphrag/simple_chunk.json` - Single chunk with extraction expected
- [ ] `test/samples/graphrag/multi_chunk.json` - Multiple chunks for merge testing
- [ ] `test/samples/graphrag/multilingual_chunks.json` - Cross-language test data
- [ ] `test/samples/graphrag/edge_cases.json` - Empty chunks, special chars, etc.

#### Mock LLM Response Patterns
- [ ] `test/samples/graphrag/mock_responses/simple_extraction.json` - Basic entity/relation
- [ ] `test/samples/graphrag/mock_responses/multi_entity.json` - Many entities
- [ ] `test/samples/graphrag/mock_responses/gleaning.json` - Multi-turn extraction
- [ ] `test/samples/graphrag/mock_responses/summarization.json` - Description merging

#### Expected Graph States
- [ ] `test/samples/graphrag/expected_graphs/simple.json` - Single chunk graph
- [ ] `test/samples/graphrag/expected_graphs/merged.json` - After chunk merging
- [ ] `test/samples/graphrag/expected_graphs/deduplicated.json` - After entity resolution

**Priority**: High
**Notes**:
1. Tests verify the complete pipeline: chunk text -> LLM extraction -> parsing -> graph construction -> merging
2. Focus on entity extraction, relation extraction, deduplication, and graph structure integrity
3. Test both happy path and edge cases (empty chunks, special characters, multilingual)
4. Use conftest.py mocking pattern from existing graphrag tests
**Task**: Fix `test_paser_documents.py` (typo in filename) to verify chunks are searchable and chat-capable
**Source File(s)**: 
- `test/testcases/test_web_api/test_document_app/test_paser_documents.py` (original, typo in name)
- `test/testcases/test_web_api/test_parse_documents.py` (new, fixed name)
**Needed Artifacts**:

### Test Documents of Various Sizes
- [ ] `test/samples/documents/txt/tiny.txt` - Tiny text file (100 bytes) - Expected: 1-2 chunks
- [ ] `test/samples/documents/txt/small.txt` - Small text file (1KB) - Expected: 3-5 chunks
- [ ] `test/samples/documents/txt/medium.txt` - Medium text file (10KB) - Expected: 10-20 chunks
- [ ] `test/samples/documents/txt/large.txt` - Large text file (100KB) - Expected: 50-100 chunks
- [ ] `test/samples/documents/txt/multilingual.txt` - Text file with EN, ZH, JA content - Expected: variable chunks

### Expected Chunk Counts per Document Type
| Document Type | Size | Expected Min Chunks | Expected Max Chunks | Notes |
|--------------|------|---------------------|---------------------|-------|
| TXT (tiny) | 100B | 1 | 2 | Single paragraph |
| TXT (small) | 1KB | 3 | 5 | Multiple paragraphs |
| TXT (medium) | 10KB | 10 | 20 | Multiple sections |
| TXT (large) | 100KB | 50 | 100 | Document with many sections |
| TXT (multilingual) | 5KB | 5 | 15 | Mixed language content |

### Mock Embedding Vectors (for search verification)
- [ ] `test/samples/mocks/embedding_vectors.json` - Pre-computed embedding vectors for search tests
  - Format: `{"query": "...", "vector": [...], "expected_top_k_doc_ids": [...]}`
  - Include at least 5 different queries with expected results
- [ ] `test/samples/mocks/mock_embedding_model.py` - Mock embedding model for unit tests
  - Returns deterministic embeddings based on input text
  - No external API calls required

### Chat Capability Test Data
- [ ] `test/samples/chat/expected_chunk_retrieval.json` - Expected chunks for specific queries
  - Format: `{"query": "...", "expected_chunk_ids": [...], "min_similarity": 0.X}`
- [ ] `test/samples/chat/sample_conversations.json` - Sample conversation contexts for chat tests
  - Format: `{"context": "...", "query": "...", "expected_response_keys": [...]}`

**Priority**: High
**Notes**: 
1. Original test file had typo in name (`paser` → `parse`)
2. New test file includes enhanced validation:
   - Chunk creation verification via `validate_chunks_created()`
   - Searchability verification via `validate_chunks_searchable()`
   - Chat capability verification via `validate_chunks_chat_capable()`
3. Tests verify that parsed documents produce chunks that are:
   - Properly stored in the database
   - Searchable via vector similarity
   - Capable of being retrieved during chat operations
4. All new validation functions added to existing test classes to maintain backward compatibility

---

### Agent 10: GraphRAG Entity Resolution Test Specialist
**Task**: Create unit tests for entity_resolution.py verifying entity merging accuracy
**Source File(s)**: rag/graphrag/entity_resolution.py
**Needed Artifacts**:
- [x] Entity fixture pairs with expected merge decisions (defined in test file)
- [x] Mock LLM responses for entity resolution (defined in test file)
- [x] Large entity dataset for performance testing (defined in test file)
**Priority**: High
**Notes**: Tests cover similarity matching (exact, case-insensitive, alias, acronym, partial match), digit difference detection, Chinese entity support, LLM-based resolution, clustering, and edge cases. All fixtures defined inline in test file.

---

### Agent 1: E2E Full RAG Pipeline Test
**Task**: Create end-to-end integration test for the complete RAG pipeline
**Source File(s)**: api/apps/kb_app.py, api/apps/document_app.py, api/apps/dialog_app.py
**Needed Artifacts**:
- [ ] Sample document(s) for testing (txt/pdf format) - can use utils.file_utils.create_txt_file
- [ ] Test environment configuration (DB, LLM mock) - already exists via fixtures
- [ ] Expected response fixtures for validation
**Priority**: Critical
**Notes**: Needs async polling for parsing completion. Uses existing common.py helpers.

---

### Agent 2: E2E Multimodal Flow Test
**Task**: Create integration tests for image-to-chat and table-to-chat workflows
**Source File(s)**: deepdoc/parser/, rag/flow/
**Needed Artifacts**:
- [ ] Test data created at runtime via utils.file_utils: create_image_file(), create_excel_file(), create_txt_file()
- [ ] Backend services running (MySQL, ES/Infinity, Redis, MinIO)
- [ ] LLM configured (for vision model in image processing)
**Priority**: Critical
**Notes**: Tests image upload → OCR → chunks, table extraction → indexing → retrieval, mixed content flow.

---

### Agent 4: Agent Switch Component Test
**Task**: Create comprehensive unit tests for Switch component operators
**Source File(s)**: agent/component/switch.py
**Needed Artifacts**:
- [x] MockCanvas class - implemented in test file
- [x] Dependencies: agent.component.base, common.connection_utils
**Priority**: High
**Notes**: 27 test methods covering all operators (contains, starts_with, ends_with, ==, !=, >=, <=, >, <, empty, not_empty) and edge cases.

---

### Agent 11: GraphRAG Construction Test
**Task**: Create tests for end-to-end graph extraction pipeline
**Source File(s)**: rag/graphrag/general/extractor.py, graph_extractor.py, index.py
**Needed Artifacts**:
- [x] Uses internal utility functions (handle_single_entity_extraction, graph_merge, tidy_graph, clean_str)
- [x] Uses mock_llm fixture for LLM mocking
**Priority**: High
**Notes**: Test file already exists with comprehensive coverage.

---

### Agent 12: GraphRAG OOM Protection Test
**Task**: Create tests for graph size limits and memory-efficient loading
**Source File(s)**: rag/graphrag/memory.py (existing module)
**Needed Artifacts**:
- [x] Uses existing GraphMemoryMonitor, check_memory_limits(), truncate_graph(), iter_graph_chunks()
- [x] Uses mock memory profiler rather than actual system memory
**Priority**: High
**Notes**: 18 tests pass. Uses fixed constants for memory estimation (avg_node_attrs=3, bytes_per_attr=100).

---

### Agent 13: DB Migration Test
**Task**: Create tests verifying schema upgrades in migrate_db()
**Source File(s)**: api/db/db_models.py
**Needed Artifacts**:
- [ ] In-memory SQLite database (:memory:)
- [ ] Fixtures: in_memory_db, test_model
- [ ] Mocked settings: DATABASE_TYPE patched to "MYSQL"
- [ ] Mocked User model for isolation
**Priority**: High
**Notes**: Tests timed out due to heavy imports in db_models.py (connects to DB on import).

---

### Agent 15: DB Service SQLite Transition
**Task**: Replace _FakeQuery/_FieldStub mocks with in-memory SQLite
**Source File(s)**: test/unit_test/api/db/services/
**Needed Artifacts**:
- [x] SQLite models: _SqliteDocument, _SqliteUserCanvas, _SqliteFile2Document, _SqliteFile
- [x] Fixtures: sqlite_db, sample_documents, sample_documents_multiple_kb
**Priority**: Medium
**Notes**: 11 tests demonstrate SQLite replaces fake query patterns. Tests pass successfully.

---

### Agent 19: API Status Code Assertions
**Task**: Update common.py to properly handle status codes
**Source File(s)**: test/testcases/test_web_api/common.py
**Needed Artifacts**:
- [x] New assertion helpers: assert_status_422(), assert_status_500(), assert_status_in()
- [x] api_call() generic helper returning (status_code, json_data) tuple
- [x] PATTERNS.md documentation created
**Priority**: High
**Notes**: Removed duplicate function definitions. expected_status parameter is opt-in for backward compatibility.

---

### Agent 21: DeepDoc Parser Tests
**Task**: Create unit tests for DocxParser, ExcelParser, PPTParser
**Source File(s)**: deepdoc/parser/docx_parser.py, excel_parser.py, ppt_parser.py
**Needed Artifacts**:
- [x] All dependencies already in project
- [ ] Potential PIL issue in image test fixture for DOCX
**Priority**: Medium
**Notes**: DOCX: 26/27 pass (1 PIL issue). Excel: 36 tests (fixed import rag.nlp issue). PPT: 28 tests all pass.

---

### Agent 23: Edge Case Document Tests
**Task**: Create tests for empty, whitespace-only, extreme UTF-8 documents
**Source File(s)**: rag/flow/
**Needed Artifacts**:
- [x] Uses File and FileParam from rag/flow/file.py
- [x] Uses MockCanvas with _doc_id and callback attributes
- [x] Uses asyncio.run() for async methods
**Priority**: Medium
**Notes**: Tests use mocking. File class passes through file metadata, doesn't process content.

---

### Agent A: Additional Tests (DSL Parsing, Race Conditions, etc.)
**Source File(s)**: agent/canvas.py, agent/component/
**Needed Artifacts**:
- [x] test/unit_test/agent/test_dsl_parsing.py - Created (module import issues in test environment)
- [x] test/unit_test/agent/component/test_categorize.py - Already exists
- [x] test/unit_test/agent/component/test_loop.py - Already exists
- [x] test/unit_test/agent/test_canvas_race_conditions.py - Already exists
- [x] test/unit_test/rag/graphrag/test_entity_resolution.py - Already exists
**Priority**: Medium

---

### Agent B: Additional Tests (Retry, Conftest, Utilities, etc.)
**Source File(s)**: rag/llm/, test/unit_test/rag/, test/utils/
**Needed Artifacts**:
- [x] test/unit_test/rag/llm/test_retry_mechanism.py - Created
- [x] test/unit_test/rag/conftest_refactored.py - Created
- [x] test/testcases/test_web_api/web_api_refactor_analysis.md - Created
- [x] test/utils/llm_mocks.py, assertions.py, fixtures.py, __init__.py - Created
- [x] Multi-tenant isolation, golden samples, chunking tests - Already exist
**Priority**: Medium
