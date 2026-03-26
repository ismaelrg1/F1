from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.powerups import PowerUp
from app.domain.powerups.ports import PowerupRepository


class SqlAlchemyPowerupRepository(PowerupRepository):
    def __init__(self, session: Session):
        self._session = session

    def list_powerups(self):
        stmt = select(PowerUp).order_by(PowerUp.id.asc())
        return list(self._session.execute(stmt).scalars().all())
