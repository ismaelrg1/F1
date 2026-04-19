from app.db.schema import Base


def test_metadata_bootstrap_registers_core_tables() -> None:
    table_names = set(Base.metadata.tables.keys())

    assert "auth.users" in table_names
    assert "competition.seasons" in table_names
    assert "betting.bets" in table_names
