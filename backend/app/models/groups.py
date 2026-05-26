from uuid import UUID

from pydantic import BaseModel

from app.db.social.group_membership import GroupRole


class GroupRead(BaseModel):
    public_id: UUID
    name: str
    role: GroupRole | None = None
    teams_enabled: bool


class GroupsResponse(BaseModel):
    items: list[GroupRead]