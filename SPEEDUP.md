# RAGFlow Performance Optimizations

Sorted by highest impact to speed. Priority flags: `[CRITICAL]`, `[HIGH]`, `[MEDIUM]`, `[LOW]`

---

## CRITICAL - Bugs Causing Major Performance Issues

### 1. Storage Connectors Never Retry (range(1) Bug)
| File | Lines | Issue |
|------|-------|-------|
| rag/utils/minio_conn.py | 169, 213 | `for _ in range(1)` = executes once, no retry |
| rag/utils/s3_conn.py | 136, 160, 186 | Same issue |
| rag/utils/oss_conn.py | 117, 141, 167 | Same issue |
| rag/utils/gcs_conn.py | 101 | Same issue |
| rag/utils/azure_spn_conn.py | 80 | Same issue |
| rag/utils/azure_sas_conn.py | 70, 88 | Same issue |

**Fix**: Change `range(1)` to `range(3)` for actual retry capability.

### 2. OpenDAL Operator Recreated on Every Delete
| File | Line | Issue |
|------|------|-------|
| rag/utils/opendal_conn.py | 86-88 | `self._operator.__init__()` called after every delete |

**Fix**: Remove the operator reinitialization - operator should be reused.

### 3. Elasticsearch Single Connection (No Pooling)
| File | Lines | Issue |
|------|-------|-------|
| common/doc_store/es_conn_pool.py | 65-66 | Returns single connection, no actual pooling |

**Fix**: Implement connection pool with multiple connections.

---

## HIGH IMPACT - Significant Speed Improvements

### 4. N+1 Query Patterns
| File | Lines | Issue |
|------|-------|-------|
| api/apps/services/dataset_api_service.py | 103, 118 | Fetches all KBs then loops |
| api/apps/sdk/session.py | 773, 785 | Fetches all then loops for delete |
| api/apps/sdk/doc.py | 768 | Same pattern |
| api/db/services/document_service.py | 1003-1067 | Task query per document in progress sync |

**Fix**: Use batch queries with `IN` clauses.

### 5. ES Bulk Size Too Small
| File | Line | Current | Fix |
|------|------|---------|-----|
| rag/graphrag/utils.py | 589 | `es_bulk_size = 4` | Increase to 50-100 |

### 6. Synchronous HTTP Calls in Async Context
| File | Lines | Issue |
|------|-------|-------|
| api/apps/auth/oauth.py | 63-79 | Uses sync `sync_request` |
| api/apps/auth/github.py | 36-52 | Two sync API calls |
| rag/llm/embedding_model.py | 365, 366, 643, etc. | Blocking `httpx.post()` |
| rag/llm/chat_model.py | 145, 146, 740, 876 | Same |

**Fix**: Use `httpx.AsyncClient` or `aiohttp`.

### 7. asyncio.run() Blocking Event Loop
| File | Line | Issue |
|------|------|-------|
| rag/graphrag/general/extractor.py | 95 | `asyncio.run(self._llm.async_chat(...))` in sync method |
| rag/flow/parser/parser.py | 913 | `asyncio.run(cv_mdl.async_chat(...))` in async context |

**Fix**: Make methods async and use `await` directly.

### 8. Duplicate Checks Fetching All Records
| File | Line | Issue |
|------|-------|-------|
| api/apps/document_app.py | 690 | Fetches all docs to check duplicate names |
| api/apps/dialog_app.py | 51 | Fetches all dialogs to check duplicates |

**Fix**: Use database COUNT/EXISTS queries.

### 9. No Embedding Cache in GraphRAG Retrieval
| File | Lines | Issue |
|------|-------|-------|
| rag/graphrag/search.py | 104-120 | Embeddings computed every query |

**Fix**: Add Redis cache for embeddings.

### 10. O(n²) Entity Pair Generation Without Limits
| File | Line | Issue |
|------|------|-------|
| rag/graphrag/entity_resolution.py | 86-95 | Generates all pairs before filtering |

**Fix**: Add early pruning and limit combinations.

### 11. Missing Database Composite Indexes
| Model | Missing Indexes |
|-------|-----------------|
| Document | (kb_id, status), (kb_id, run), (kb_id, progress) |
| Task | (doc_id, progress), (doc_id, task_type) |
| Conversation | (dialog_id, user_id) |
| Knowledgebase | (tenant_id, status), (tenant_id, permission) |

---

## MEDIUM IMPACT - Noticeable Speed Improvements

### 12. Blocking time.sleep() in Async Contexts
| File | Lines | Count |
|------|-------|-------|
| rag/llm/embedding_model.py | 419, 436, 1119 | 3 |
| rag/llm/sequence2txt_model.py | 219, 325 | 2 |
| rag/llm/cv_model.py | 749, 761 | 2 |
| agent/tools/*.py | - | 12+ files |
| rag/utils/circuit_breaker.py | - | Various |

**Fix**: Replace with `asyncio.sleep()` in async contexts.

### 13. No LLM/Embedding Response Caching
| File | Issue |
|------|-------|
| rag/llm/chat_model.py | No caching for repeated requests |
| rag/llm/embedding_model.py | No caching for embeddings |

**Fix**: Implement LRU caching for common queries.

### 14. Connection Pooling Issues
| File | Issue |
|------|-------|
| rag/llm/embedding_model.py | New client created per instance |
| rag/llm/chat_model.py | Same issue |

**Fix**: Use shared client instances with connection pooling.

### 15. Inefficient update_many_by_id
| File | Lines | Issue |
|------|-------|-------|
| api/db/services/common_service.py | 245-263 | N individual updates instead of batch |

**Fix**: Use single UPDATE with CASE WHEN.

### 16. Regex Patterns Not Precompiled
| File | Lines | Issue |
|------|-------|-------|
| rag/flow/parser/parser.py | 533, 590, 1298-1315 | Regex compiled every call |
| rag/flow/hierarchical_merger/hierarchical_merger.py | 91-102 | Same |

**Fix**: Precompile and cache patterns at initialization.

### 17. Repeated Tokenization
| File | Lines | Issue |
|------|-------|-------|
| api/apps/chunk_app.py | Multiple | Same content tokenized repeatedly |

**Fix**: Store pre-tokenized values in database.

### 18. Bucket Existence Check on Every Put
| File | Line | Issue |
|------|------|-------|
| rag/utils/minio_conn.py | 148 | Extra network call per operation |
| rag/utils/s3_conn.py | 138 | Same |
| rag/utils/oss_conn.py | 119 | Same |

**Fix**: Cache bucket existence with TTL.

---

## LOW IMPACT - Minor Optimizations

### 19. Frontend React Memoization
| Component | File | Priority |
|-----------|------|----------|
| AssistantGroupButton | web/src/components/message-item/group-button.tsx:35 | HIGH |
| UserGroupButton | web/src/components/message-item/group-button.tsx:144 | HIGH |
| ChatList | web/src/pages/home/chat-list.tsx:11 | HIGH |
| Agents | web/src/pages/home/agent-list.tsx:10 | HIGH |
| +10 more | Various | MEDIUM |

**Fix**: Wrap with `React.memo()`.

### 20. Frontend Lazy Loading
| Library | Size | Files |
|---------|------|-------|
| monaco-editor | ~2.5MB | 14 |
| SyntaxHighlighter | ~200KB | 6 |
| @antv/g6 | ~500KB | 3 |

**Fix**: Use dynamic imports.

### 21. Frontend Key Prop Issues
| File | Lines | Issue |
|------|-------|-------|
| web/src/pages/next-search/search-view.tsx | 205, 274 | Using array index as key |

**Fix**: Use stable identifiers (chunk.chunk_id).

### 22. Docker Resource Limits Missing
| Service | File | Issue |
|---------|------|-------|
| litellm | docker-compose.yml | No memory/CPU limits |
| mysql | docker-compose-base.yml | No resource limits |

**Fix**: Add deploy.resources.limits.

### 23. Nginx gzip Disabled
| File | Issue |
|------|-------|
| docker/nginx/nginx.conf | gzip commented out |

**Fix**: Enable gzip compression.

### 24. MySQL Tuning Missing
| Setting | Current | Recommended |
|---------|---------|--------------|
| innodb_buffer_pool_size | Not set | 1G |
| innodb_log_file_size | Not set | 256M |

---

## LOCAL_DEPLOYMENT Optimizations (Safe for Home Use)

When `LOCAL_DEPLOYMENT=true`, these safe optimizations apply:

### 25. Connection Pool Overhead Reduction
```python
# Smaller pool for local dev
min_connections: 1
max_connections: 3
```

### 26. In-Memory Caching
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_cached_tenant_info(tenant_id):
    pass
```

### 27. Thread Pool Size Increase
```python
# agent/canvas.py line 93
ThreadPoolExecutor(max_workers=10)  # vs 5
```

### 28. Larger Batch Sizes
```bash
export ES_BULK_SIZE=100
export MAX_CONCURRENT_PROCESS_AND_EXTRACT_CHUNK=20
```

### 29. Container Reuse (Already Implemented)
- agent/sandbox/executor_manager/core/container.py:165-185 uses LOCAL_DEPLOYMENT to skip container recreation

---

## Priority Action List

### Phase 1: Critical Bugs (Fix Immediately)
- [ ] Fix `range(1)` retry bug in all storage connectors
- [ ] Remove OpenDAL operator reinitialization
- [ ] Implement ES connection pooling

### Phase 2: High Impact (This Sprint)
- [ ] Fix N+1 queries in dataset_api_service.py
- [ ] Increase ES bulk size from 4 to 50-100
- [ ] Convert sync HTTP to async in auth modules
- [ ] Add database composite indexes
- [ ] Add embedding cache in GraphRAG

### Phase 3: Medium Impact (Next Sprint)
- [ ] Replace time.sleep with asyncio.sleep
- [ ] Add LLM response caching
- [ ] Optimize update_many_by_id
- [ ] Precompile regex patterns

### Phase 4: Low Impact (Backlog)
- [ ] Add React.memo to components
- [ ] Lazy load Monaco/SyntaxHighlighter
- [ ] Add Docker resource limits
- [ ] Enable nginx gzip

---

## Files to Modify

### Critical
- `rag/utils/minio_conn.py`
- `rag/utils/s3_conn.py`
- `rag/utils/oss_conn.py`
- `rag/utils/gcs_conn.py`
- `rag/utils/opendal_conn.py`
- `common/doc_store/es_conn_pool.py`

### High Priority
- `api/apps/services/dataset_api_service.py`
- `api/apps/sdk/session.py`
- `api/apps/sdk/doc.py`
- `api/db/services/document_service.py`
- `rag/graphrag/utils.py`
- `api/apps/auth/oauth.py`
- `api/apps/auth/github.py`
- `rag/graphrag/search.py`
- `rag/graphrag/entity_resolution.py`
- `api/db/db_models.py`

### Medium Priority
- `rag/llm/embedding_model.py`
- `rag/llm/chat_model.py`
- `rag/flow/parser/parser.py`
- `rag/graphrag/general/extractor.py`
- `api/db/services/common_service.py`
- `api/apps/chunk_app.py`

### Low Priority
- `web/vite.config.ts`
- `docker/docker-compose.yml`
- `docker/docker-compose-base.yml`
- `docker/nginx/nginx.conf`
