from fastapi import APIRouter

router = APIRouter()


@router.get("")
def list_circuits() -> dict:
    return {
        "items": [
            {
                "id": 7,
                "code": "monaco",
                "name": "Circuit de Monaco",
                "country_id": 2,
                "map_asset_url": "https://example.com/circuits/monaco_map.png",
                "image_asset_url": "https://example.com/circuits/monaco_photo.jpg",
            }
        ]
    }
