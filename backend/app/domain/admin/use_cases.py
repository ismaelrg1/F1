class PublishResults:
    def execute(self, user_id: int) -> dict:
        return {"published_by": user_id}
