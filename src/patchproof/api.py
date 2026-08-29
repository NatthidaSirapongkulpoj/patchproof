from fastapi import FastAPI

app = FastAPI(
    title="PatchProof",
    description="Verification-first agentic repair for Python APIs",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
