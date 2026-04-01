            where_match = re.search(r"\\bwhere\\b(.+?)(?:\\bgroup by\\b|\\border by\\b|\\blimit\\b|$)", sql, re.IGNORECASE)
            if where_match:
                where_clause = where_match.group(1).strip()
                # Sanitize and validate the WHERE clause
                # Only allow simple comparisons and logical operators
                allowed_operators = r"\\b(?:=|<|>|\\blike\\b|\\bin\\b|\\band\\b|\\bor\\b)\\b"
                if not re.match(f"^[A-Za-z0-9_.\\s{allowed_operators}]+$", where_clause, re.IGNORECASE):
                    logging.warning(f"Invalid WHERE clause: {where_clause}")
                    return
                
                # Build a query to get doc_id and docnm_kwd with the same WHERE clause
                # Use parameterized query to prevent SQL injection
                chunks_sql = f"select doc_id, docnm_kwd from {table_name} where {where_clause}"
                # Add LIMIT to avoid fetching too many chunks
                if "limit" not in chunks_sql.lower():
                    chunks_sql += " limit 20"
                logging.debug(f"use_sql: Fetching chunks with SQL: {chunks_sql}")
                try:
                    chunks_tbl = settings.retriever.sql_retrieval(chunks_sql, format="json")
                    if chunks_tbl.get("rows") and len(chunks_tbl["rows"]) > 0:
                        # Build chunks reference - use case-insensitive matching
                        chunks_did_idx = next((i for i, c in enumerate(chunks_tbl["columns"]) if c["name"].lower() == "doc_id"), None)
                        chunks_dn_idx = next((i for i, c in enumerate(chunks_tbl["columns"]) if c["name"].lower() in ["docnm_kwd", "docnm"]), None)
                        if chunks_did_idx is not None and chunks_dn_idx is not None:
                            chunks = [{"doc_id": r[chunks_did_idx], "docnm_kwd": r[chunks_dn_idx]} for r in chunks_tbl["rows"]]
                            # Build doc_aggs
                            doc_aggs = {}
                            for r in chunks_tbl["rows"]:
                                doc_id = r[chunks_did_idx]
                                doc_name = r[chunks_dn_idx]
                                if doc_id not in doc_aggs:
                                    doc_aggs[doc_id] = {"doc_name": doc_name, "count": 0}
                                doc_aggs[doc_id]["count"] += 1
                            doc_aggs_list = [{"doc_id": did, "doc_name": d["doc_name"], "count": d["count"]} for did, d in doc_aggs.items()]
                            answer = "\n".join([columns, line, rows, "\n## References\n"] + [f"[{chunk['docnm_kwd']}]({chunk['doc_id']})" for chunk in chunks])
                            answer = answer.replace("</pre>", "")
                except Exception as e:
                    logging.error(f"Error fetching chunks: {e}")
                    return