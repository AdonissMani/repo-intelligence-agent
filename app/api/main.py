from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from app.db.registry import load_registry
from app.routing.router import RepositoryRouter


class RouteRequest(BaseModel):
    question: str
    strategy: str = "hybrid"
    limit: int = 5


app = FastAPI(title="Enterprise Repo Intelligence")


@app.post("/route")
def route(request: RouteRequest):
    repositories, relationships = load_registry()
    router = RepositoryRouter(repositories, relationships)
    results, stats = router.route(request.question, request.strategy, request.limit)
    return {
        "repositories": [result.__dict__ for result in results],
        "strategy": request.strategy,
        "stats": stats,
    }
