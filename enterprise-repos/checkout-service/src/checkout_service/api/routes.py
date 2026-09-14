from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health():
    return {"service": "checkout-service", "status": "ok"}
