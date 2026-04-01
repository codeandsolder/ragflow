# Test Artifacts Required

This document lists all artifacts needed for testing RAGFlow, organized by category and priority.

---

## Priority: High

### Test Files (Already Created)
| File | Status | Notes |
|------|--------|-------|
| `test/unit_test/agent/test_state_persistence.py` | ✅ Done | 6 tests for LOCAL_DEPLOYMENT toggle |
| `test/unit_test/rag/graphrag/test_entity_resolution.py` | ✅ Done | Entity merging accuracy tests |
| `test/unit_test/agent/test_dsl_parsing.py` | ✅ Done | DSL parsing tests |
| `test/unit_test/agent/component/test_categorize.py` | ✅ Done | Categorize component tests |
| `test/unit_test/agent/component/test_loop.py` | ✅ Done | Loop component tests |
| `test/unit_test/agent/test_canvas_race_conditions.py` | ✅ Done | Race condition tests |
| `test/unit_test/rag/llm/test_retry_mechanism.py` | ✅ Done | Retry and circuit breaker tests |
| `test/unit_test/api/db/test_sqlite_services.py` | ✅ Done | SQLite service tests |
| `test/testcases/test_web_api/common.py` | ✅ Done | Status code assertion helpers |
| `test/utils/` | ✅ Done | llm_mocks.py, assertions.py, fixtures.py |

### Fixtures Needed for GraphRAG Tests
| File | Description |
|------|-------------|
| `test/unit_test/rag/graphrag/fixtures/large_graph_1000_nodes.json` | Graph with 1000 nodes, ~5000 edges for stress testing |
| `test/unit_test/rag/graphrag/fixtures/large_graph_5000_nodes.json` | Graph with 5000 nodes for OOM simulation |
| `test/unit_test/rag/graphrag/fixtures/chunked_graphs/` | Pre-chunked subgraphs for memory-efficient loading |
| `test/unit_test/rag/graphrag/fixtures/config_max_nodes_1000.json` | Config with max_nodes=1000 |
| `test/unit_test/rag/graphrag/fixtures/config_max_memory_512mb.json` | Config with max_memory=512MB |
| `test/unit_test/rag/graphrag/mock_memory_profiler.py` | Mock memory profiling utility |
| `test/unit_test/rag/graphrag/fixtures/edge_cases/empty_graph.json` | Empty graph fixture |
| `test/unit_test/rag/graphrag/fixtures/edge_cases/single_node_graph.json` | Single node graph fixture |
| `test/unit_test/rag/graphrag/fixtures/edge_cases/dense_graph.json` | Fully connected dense graph |

### Sample Documents for Parser Tests
| File | Description | Expected Chunks |
|------|-------------|-----------------|
| `test/samples/documents/txt/tiny.txt` | 100 bytes | 1-2 |
| `test/samples/documents/txt/small.txt` | 1KB | 3-5 |
| `test/samples/documents/txt/medium.txt` | 10KB | 10-20 |
| `test/samples/documents/txt/large.txt` | 100KB | 50-100 |
| `test/samples/documents/txt/multilingual.txt` | EN, ZH, JA | 5-15 |
| `test/samples/documents/pdf/sample_simple.pdf` | Plain text paragraphs | — |
| `test/samples/documents/pdf/sample_with_images.pdf` | Embedded images | — |
| `test/samples/documents/pdf/sample_with_tables.pdf` | Table structures | — |
| `test/samples/documents/pdf/sample_multilingual.pdf` | EN, ZH, JA | — |
| `test/samples/documents/docx/sample_simple.docx` | Simple Word doc | — |
| `test/samples/documents/docx/sample_with_tables.docx` | Word with tables | — |
| `test/samples/documents/xlsx/sample_simple.xlsx` | Simple spreadsheet | — |
| `test/samples/documents/xlsx/sample_with_formulas.xlsx` | Excel with formulas | — |
| `test/samples/documents/pptx/sample_simple.pptx` | Simple presentation | — |

### Images for OCR Tests
| File | Description |
|------|-------------|
| `test/samples/images/sample_text.png` | Image containing text |
| `test/samples/images/sample_table.png` | Image containing table data |
| `test/samples/images/sample_chart.png` | Image containing chart/graph |

### GraphRAG Test Data
| File | Description |
|------|-------------|
| `test/samples/graphrag/simple_chunk.json` | Single chunk with known entities |
| `test/samples/graphrag/multi_chunk.json` | Multiple chunks for merge testing |
| `test/samples/graphrag/multilingual_chunks.json` | Cross-language test data |
| `test/samples/graphrag/edge_cases.json` | Empty chunks, special chars |
| `test/samples/graphrag/mock_responses/simple_extraction.json` | Basic entity/relation response |
| `test/samples/graphrag/mock_responses/multi_entity.json` | Many entities response |
| `test/samples/graphrag/mock_responses/gleaning.json` | Multi-turn extraction |
| `test/samples/graphrag/mock_responses/summarization.json` | Description merging |
| `test/samples/graphrag/expected_graphs/simple.json` | Single chunk graph |
| `test/samples/graphrag/expected_graphs/merged.json` | After chunk merging |
| `test/samples/graphrag/expected_graphs/deduplicated.json` | After entity resolution |

### Chat/Search Test Data
| File | Description |
|------|-------------|
| `test/samples/mocks/embedding_vectors.json` | Pre-computed embeddings for search tests (5+ queries) |
| `test/samples/mocks/mock_embedding_model.py` | Mock embedding model for unit tests |
| `test/samples/chat/expected_chunk_retrieval.json` | Expected chunks for specific queries |
| `test/samples/chat/sample_conversations.json` | Sample conversation contexts |

### Expected Output Files
| File | Description |
|------|-------------|
| `test/samples/expected_outputs/pdf_simple.json` | PDF simple extraction |
| `test/samples/expected_outputs/pdf_with_tables.json` | Table extraction |
| `test/samples/expected_outputs/docx_simple.json` | DOCX extraction |
| `test/samples/expected_outputs/xlsx_simple.json` | XLSX extraction |
| `test/samples/expected_outputs/image_text.json` | OCR output |

---

## Priority: Medium

### Additional Test Files to Create
| File | Description |
|------|-------------|
| `test/unit_test/rag/graphrag/test_chunked_loading.py` | Memory-efficient chunked graph loading |
| `test/unit_test/rag/graphrag/test_oom_protection.py` | Graph size limits and OOM handling |
| `test/testcases/test_web_api/test_parse_documents.py` | Parser integration tests |

---

## Known Issues in Existing Tests

### HIGH PRIORITY FIXES

| Test File | Issue | Fix |
|-----------|-------|-----|
| `test_e2e_rag_pipeline.py` | `create_txt_file` signature mismatch | Use actual content or remove parameter |
| `test_e2e_rag_pipeline.py` | `pytest.request.addfinalizer` | Fix to `request.addfinalizer` |
| `test_e2e_multimodal.py` | Missing import at line 199 | Add `create_txt_file` import |
| `test_state_persistence.py` | Test logic doesn't verify file/env persistence | Rewrite to actually test persistence |
| `test_state_persistence.py` | Missing "on" in env parsing values | Add "on" to parametrized values |
| `test_migrations.py` | Mock patches after import | Move patches before import |
| `test_migrations.py` | Silent exception handling | Remove try/except pass |
| `test_sqlite_services.py` | Missing BaseModel fields | Add create_time, update_time |
| `test_sqlite_services.py` | Missing JSONField test | Add parser_config JSON test |
| `test_edge_case_documents.py` | String "File" as ID | Use proper ID pattern |
| `test_edge_case_documents.py` | Escaped string instead of actual null bytes | Use actual null bytes |
| `test_dsl_parsing.py` | Missing branching flow tests | Add categorize/switch tests |
| `test_dsl_parsing.py` | Missing parallel execution tests | Add parallel component tests |
| `test_dsl_parsing.py` | Missing loop tests | Add iteration component tests |
| `test_retry_mechanism.py` | Missing backoff timing verification | Add actual timing tests |
| `test_retry_mechanism.py` | Missing circuit breaker tests | Add state transition tests |
| `test_memory_management.py` | Uses mocks instead of real implementation | Import actual functions |
| `test_memory_management.py` | Potential infinite loop | Add max iteration limit |

### MEDIUM PRIORITY IMPROVEMENTS

| Test File | Missing Coverage |
|-----------|------------------|
| `test_e2e_rag_pipeline.py` | Streaming, multi-turn, error handling |
| `test_e2e_multimodal.py` | Corrupted files, empty docs, network failures |
| `test_switch.py` | ≠, ≥, ≤ operators, whitespace edge cases |
| `test_graph_construction.py` | Self-referential edges, disconnected components |
| `test_migrations.py` | update_tenant_llm_to_id tests, idempotency |
| `test_parser_tests/` | Corrupted file handling, password-protected files |