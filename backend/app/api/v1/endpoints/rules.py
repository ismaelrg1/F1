from fastapi import APIRouter

router = APIRouter()


@router.get("/current")
def current_rules() -> dict:
    return {"pdf_url": "https://example.com/rules/rules_2026.pdf", "version": "2026.1", "updated_at": "2026-02-22T00:00:00Z"}
