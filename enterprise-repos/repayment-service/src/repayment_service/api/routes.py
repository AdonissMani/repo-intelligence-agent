from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health():
    return {"service": "repayment-service", "status": "ok"}
