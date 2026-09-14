# repo-intelligence-agent

## Enterprise Repo Intelligence

A working research prototype for routing natural-language engineering questions to the smallest relevant slice of a simulated enterprise software ecosystem.

## Quick start

```bash
python3 -m app.seed
python3 -m evaluation.evaluate_routing
python3 -m unittest discover
uvicorn app.api.main:app --reload
```

If FastAPI dependencies are not installed yet, use the stdlib route server:

```bash
python3 -m app.api.simple_server
curl -s http://127.0.0.1:8000/route -d '{"question":"Where is refund eligibility decided?"}'
```

Docker Compose provides PostgreSQL/pgvector, and `app/db/schema.sql` defines the initial registry tables. The current deterministic prototype also stores its registry in `data/registry.json` so evaluation can run without external services.

## Retrieval Experiments

The router supports independently selectable strategies:

- `lexical`: local BM25 over repository-level text
- `semantic`: embedding similarity through the configured `EmbeddingProvider`
- `metadata`: generic metadata field overlap
- `graph`: seed selection plus configurable graph traversal
- `hybrid`: weighted combination of lexical, semantic, metadata, and graph signals

Offline runs use the deterministic hashing embedding provider:

```bash
REPO_INTEL_EMBEDDING_PROVIDER=hashing python3 -m evaluation.evaluate_routing
```

Real semantic embedding experiments can use the semantic adapter when credentials are available:

```bash
OPENAI_API_KEY=... REPO_INTEL_EMBEDDING_PROVIDER=semantic python3 -m evaluation.evaluate_routing
```

Graph experiments are reported at depths `0`, `1`, `2`, and `3`. Per-question records, including predicted repositories and graph paths, are written to `experiments/`.
