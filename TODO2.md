# RAGFlow Project Review & Roadmap (TODO2.md)

This document outlines critical issues, performance bottlenecks, and architectural improvements identified during a multi-agent parallel code review conducted on March 27, 2026.

---

## 🔴 CRITICAL & HIGH PRIORITY (Security & Stability)

### 1. Security & Isolation
- [ ] **Sandbox Escape & Lateral Movement**:
    - [ ] **Container Reuse**: Sandbox containers are reused without being destroyed. Persistent background processes from one task can access data from the next. *Fix: Implement "fresh container per request" or "one-time use" lifecycle.*
    - [ ] **Network Isolation**: Sandbox containers currently have network access. *Fix: Add `--network none` to `docker run` in `container.py` to prevent SSRF against internal DBs.*
    - [ ] **Privileged Manager**: `executor_manager` runs with `privileged: true` and mounts `/var/run/docker.sock`. *Fix: Remove privileged mode and use a restricted Docker API proxy.*
- [ ] **API Vulnerabilities**:
    - [ ] **IDOR (Insecure Direct Object Reference)**: Legacy endpoints (`kb_app.py`, `document_app.py`) lack ownership checks. *Fix: Implement a mandatory `@resource_owner_required` decorator.*
    - [ ] **Text-to-SQL Injection**: AI-generated SQL is executed without strict validation. *Fix: Use `sqlglot` to enforce `SELECT` only and whitelist tables/columns.*
    - [ ] **Broken Access Control**: Commented out `@login_required` on `thumbnails` and `get_image` endpoints. *Fix: Re-enable authentication immediately.*
    - [ ] **SSRF in Web Crawl**: `web_crawl` accepts arbitrary URLs. *Fix: Block private/reserved IP ranges.*

### 2. Core Logic & Race Conditions
- [ ] **Agent Workflow Race Conditions**: Concurrent access to `Canvas.globals` in `_run_batch` leads to lost updates (especially in `VariableAssigner`). *Fix: Implement `threading.Lock` for shared state access.*
- [ ] **OCR Data Loss**: `TextRecognizer` processes only the last batch of images due to an indentation bug in the inference loop. *Fix: Move inference inside the `beg_img_no` loop in `ocr.py`.*
- [ ] **GraphRAG OOM Risk**: The entire graph is loaded into memory using `networkx`. *Fix: Transition to a persistent graph store (Neo4j/NebulaGraph) for large KBs.*

---

## 🟡 MEDIUM PRIORITY (Performance & Scalability)

### 3. RAG & Parsing Efficiency
- [ ] **Synchronous I/O in Splitter**: `id2image` calls are synchronous inside loops. *Fix: Use `asyncio.gather` to parallelize image retrieval from MinIO/S3.*
- [ ] **GraphRAG $O(N^2)$ Re-indexing**: Re-generates all document subgraphs on every update. *Fix: Implement incremental indexing.*
- [ ] **Sequential Inference Bottleneck**: Layout recognition runs images individually instead of using ONNX Runtime's batch capabilities. *Fix: Stack tensors and run single batch inference.*
- [ ] **Token-Character Budget Mismatch**: Chunk overlap logic uses character slicing while the budget is in tokens. *Fix: Use token IDs for consistent slicing.*

### 4. Database & Backend Services
- [ ] **Inefficient Pagination**: Manual batch loops use `.offset().limit()`, leading to "deep pagination" performance degradation. *Fix: Use cursor-based pagination (`WHERE id > last_id`).*
- [ ] **Inefficient Document Counting**: `get_doc_count` fetches all IDs into memory. *Fix: Use native `.count()` query.*
- [ ] **Redundant Tokenization**: Repeatedly calling `num_tokens_from_string` in loops. *Fix: Cache token counts or use pre-tokenized representations.*

### 5. Frontend & UI/UX
- [ ] **Memory Leaks (SSE)**: `AbortController` is not cleared on component unmount in chat hooks. *Fix: Add `useEffect` cleanup for all SSE and fetch requests.*
- [ ] **"God Hook" Refactoring**: `logic-hooks.ts` is over 800 lines with unrelated logic. *Fix: Split into domain-specific hooks (`useChat`, `useScroll`, etc.).*
- [ ] **Type Safety**: Significant use of `any` in core chat and agent logic. *Fix: Replace with specific interfaces from `/interfaces/`.*

---

## 🟢 LOW PRIORITY (Clean Code & Infrastructure)

### 6. Architectural Debt
- [ ] **LLM/Embedding Code Duplication**: Significant boilerplate repeated across 20+ embedding providers. *Fix: Extract common retry, batching, and error handling into a `RemoteModelBase`.*
- [ ] **Circuit Breaker Coverage**: Only Chat models have circuit breakers; Embedding/Rerank lack them. *Fix: Apply `LLMCircuitBreaker` to all model types.*
- [ ] **Mixed Package Managers**: Reliance on `apt`, `uv`, `npm`, and runtime `pip`. *Fix: Move runtime installs (like `docling`) into the `Dockerfile` build stage.*

### 7. Accuracy & Tuning
- [ ] **Hardcoded Hybrid Weights**: Search defaults to 0.95 vector / 0.05 full-text, which fails for exact-match queries. *Fix: Make weights configurable per-parser.*
- [ ] **Hardcoded Vector Dimensions**: GraphRAG assumes 1024 dimensions. *Fix: Detect dimensions dynamically from the embedding model.*
- [ ] **Heuristic Metadata Extraction**: PDF author/abstract extraction uses brittle regex. *Fix: Consider a small VLM or layout-aware model.*

---

## 🛠️ Implementation Roadmap Proposal
1. **Phase 1 (Immediate)**: Fix OCR batching bug, re-enable API authentication, and patch the SQL execution vulnerability.
2. **Phase 2 (Security)**: Implement proper sandbox isolation (no network, no reuse) and add IDOR checks to legacy endpoints.
3. **Phase 3 (Scalability)**: Refactor GraphRAG for persistent storage and parallelize I/O in the document processing pipeline.
4. **Phase 4 (Refactor)**: Decouple LLM providers and decompose frontend "God Hooks".
