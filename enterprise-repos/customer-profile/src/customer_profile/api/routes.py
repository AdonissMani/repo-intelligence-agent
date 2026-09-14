from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health():
    return {"service": "customer-profile", "status": "ok"}
