from fastapi import APIRouter

router = APIRouter()


@router.get("")
def list_countries() -> dict:
    return {"items": [{"id": 1, "iso2": "ES", "name": "Spain", "flag_asset_url": "https://example.com/flags/es.png"}]}
