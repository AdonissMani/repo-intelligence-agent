from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health():
    return {"service": "payment-core", "status": "ok"}
