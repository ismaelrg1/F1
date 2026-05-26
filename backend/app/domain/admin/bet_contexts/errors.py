from app.domain.admin.errors import AdminError


class BetContextGenerationSeasonNotFoundError(AdminError):
    def __init__(self, *, season_id: int):
        self.season_id = season_id
        super().__init__()

    @property
    def context(self) -> dict:
        return {"season_id": self.season_id}

    @property
    def public_params(self) -> dict:
        return {"season_id": self.season_id}


class BetContextGenerationGroupNotFoundError(AdminError):
    def __init__(self, *, group_id: int):
        self.group_id = group_id
        super().__init__()

    @property
    def context(self) -> dict:
        return {"group_id": self.group_id}

    @property
    def public_params(self) -> dict:
        return {"group_id": self.group_id}
    
class BetContextGenerationGroupScopeRequiredError(AdminError):
    pass


class BetContextGenerationForbiddenGroupError(AdminError):
    pass