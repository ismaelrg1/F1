from app.adapters.sqlalchemy.bets.base_repository import SqlAlchemyBetBaseRepository
from app.domain.bets.ports import BetQuestionsRepository


class SqlAlchemyBetQuestionsRepository(SqlAlchemyBetBaseRepository, BetQuestionsRepository):
    pass
