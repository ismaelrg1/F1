from pydantic import BaseModel


class PublishResultsResponse(BaseModel):
    published_by: int
