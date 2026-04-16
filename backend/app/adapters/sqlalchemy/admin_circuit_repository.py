from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.competition import Circuit, Country
from app.domain.admin.circuits.models import AdminCircuit, AdminCircuitCountry
from app.domain.admin.circuits.ports import AdminCircuitRepository

class SqlAlchemyAdminCircuitRepository(AdminCircuitRepository):
    def __init__(self, session: Session):
        self._session = session
    
    def get_by_code(self, code: str) -> AdminCircuit | None:
        stmt = (
            select(Circuit)
            .where(Circuit.code == code)
            .options(joinedload(Circuit.country))
        )
        circuit = self._session.execute(stmt).scalar_one_or_none()
        if circuit is None:
            return None
        return self._map_circuit(circuit)
    
    def get_country_by_iso2(self, iso2: str) -> AdminCircuitCountry | None:
        stmt = select(Country).where(Country.iso2 == iso2)
        country = self._session.execute(stmt).scalar_one_or_none()
        if country is None:
            return None
        return AdminCircuitCountry(
            id=country.id,
            iso2=country.iso2,
        )
    
    def create(
        self,
        *,
        code: str,
        name: str,
        country_id: int,
        map_asset_url: str | None,
        image_asset_url: str | None,
    ) -> AdminCircuit:
        circuit = Circuit(
            code=code,
            name=name,
            country_id=country_id,
            map_asset_url=map_asset_url,
            image_asset_url=image_asset_url,
        )
        self._session.add(circuit)
        self._session.commit()

        stmt = (
            select(Circuit)
            .where(Circuit.id == circuit.id)
            .options(joinedload(Circuit.country))
        )
        created = self._session.execute(stmt).scalar_one()
        return self._map_circuit(created)
    
    def _map_circuit(self, circuit: Circuit) -> AdminCircuit:
        return AdminCircuit(
            id=circuit.id,
            code=circuit.code,
            name=circuit.name,
            country_iso2=circuit.country.iso2,
            map_asset_url=circuit.map_asset_url,
            image_asset_url=circuit.image_asset_url,
        )
