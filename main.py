from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from .game_theory import analyze
from .models import GameConfig, HealthResponse, ValidationResult

app = FastAPI(title="Game Theory Simulator API", version="1.0.0")
@app.get("/")
def root():
    return {"message": "Game Theory Simulator API. See /docs for documentation."}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

EXAMPLE = {
    "seller_a": "Seller A",
    "seller_b": "Seller B",
    "strategies_a": ["High Price", "Low Price"],
    "strategies_b": ["High Price", "Low Price"],
    "payoffs": [
        [[50, 50], [20, 70]],
        [[70, 20], [35, 35]],
    ],
}


@app.get("/api/health", response_model=HealthResponse)
def health():
    return {"status": "ok", "version": app.version}


@app.get("/api/example")
def example():
    return EXAMPLE


@app.post("/api/validate", response_model=ValidationResult)
def validate(config: dict):
    try:
        GameConfig(**config)
        return {"valid": True, "errors": []}
    except ValidationError as e:
        msgs = [
            f"{'.'.join(str(x) for x in err['loc'])}: {err['msg']}" if err["loc"] else err["msg"]
            for err in e.errors()
        ]
        return {"valid": False, "errors": msgs}
    except TypeError:
        return {"valid": False, "errors": ["Request body is not a valid configuration object."]}


@app.post("/api/analyze")
def analyze_game(config: GameConfig):
    # Invalid input is rejected automatically with HTTP 422 by Pydantic.
    return analyze(
        config.seller_a,
        config.seller_b,
        config.strategies_a,
        config.strategies_b,
        config.payoffs,
    )