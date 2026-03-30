from app.domain.admin.fastf1.ports import AdminFastF1Repository

class ListFastF1RaceEventPreviews:
    def __init__(self, repository: AdminFastF1Repository):
        self._repository = repository

    def execute(self, *, year: int):
        return self._repository.list_race_event_previews(year)
    
class ListFastF1TestingEventPreviews:
    def __init__(self, repository: AdminFastF1Repository):
        self._repository = repository

    def execute(self, *, year: int):
        return self._repository.list_testing_event_previews(year)