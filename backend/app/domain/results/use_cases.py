from app.models.results import PublishResultsRequest, ResultsQuery, ResultsUpsertRequest


class ListResults:
    def execute(self, query: ResultsQuery) -> dict:
        return {
            "context_id": query.context_id,
            "session_id": query.session_id,
            "results_published": False,
            "items": [],
        }


class UpsertResults:
    def execute(self, payload: ResultsUpsertRequest) -> dict:
        return {
            "ok": True,
            "context_id": payload.context_id,
            "event_session_id": payload.event_session_id,
            "items_count": len(payload.items),
        }


class PublishContextResults:
    def execute(self, payload: PublishResultsRequest) -> dict:
        return {
            "ok": True,
            "context_id": payload.context_id,
            "event_session_id": payload.event_session_id,
            "results_published": True,
        }
