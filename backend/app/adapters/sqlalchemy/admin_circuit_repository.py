from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.competition import Circuit, Country
from app.domain.admin.circuits.ports import AdminCircuitRepository

class SqlAlchemyAdminCircuitRepository(AdminCircuitRepository):
    def __init__(self, session: Session):
        self._session = session
    
    def get_by_code(self, code: str):
        stmt = select(Circuit).where(Circuit.code == code)
        return self._session.execute(stmt).scalar_one_or_none()
    
    def get_country_by_id(self, country_id: int):
        return self._session.get(Country, country_id)
    
    def create(
        self,
        *,
        code: str,
        name: str,
        country_id: int,
        map_asset_url: str | None,
        image_asset_url: str | None,
    ):
        circuit = Circuit(
            code=code,
            name=name,
            country_id=country_id,
            map_asset_url=map_asset_url,
            image_asset_url=image_asset_url,
        )
        self._session.add(circuit)
        self._session.commit()
        self._session.refresh(circuit)
        return circuit