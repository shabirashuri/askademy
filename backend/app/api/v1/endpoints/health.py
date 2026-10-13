from fastapi import APIRouter

router = APIRouter()


@router.get("/health", summary="Check API availability")
def get_health() -> dict[str, str]:
    return {"status": "ok"}
