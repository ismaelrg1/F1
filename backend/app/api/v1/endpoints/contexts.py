from fastapi import APIRouter

router = APIRouter()


@router.get("")
def list_contexts(season_id: int | None = None, kind: str | None = None) -> dict:
    return {
        "items": [
            {
                "id": 100,
                "kind": kind or "GP",
                "season_id": season_id or 1,
                "race_event_id": 10,
                "testing_event_id": None,
                "label": "Monaco GP",
                "results_published": False,
                "results_published_at": None,
            }
        ]
    }


@router.get("/{context_id}/status")
def context_status(context_id: int, session_id: int | None = None) -> dict:
    return {
        "context_id": context_id,
        "session_id": session_id,
        "is_open": True,
        "lock_cutoff": "2026-05-24T13:55:00Z",
        "has_submitted": False,
        "has_submitted_any_in_context": True,
        "can_view_others": False,
        "view_others_rule": "AFTER_SUBMIT_OR_LOCK",
        "results_published": False,
        "results_published_at": None,
        "can_use_powerups": False,
        "powerups_rule": "GP_ONLY_IF_NO_SUBMISSIONS",
    }


@router.get("/{context_id}/template")
def context_template(context_id: int, session_type: str | None = None) -> dict:
    return {
        "context_id": context_id,
        "session_type": session_type or "RACE",
        "items": [
            {
                "bet_score_id": 1,
                "code": "RACE_P1",
                "label": "Ganador",
                "base_points": 5,
                "value_type": "DRIVER",
                "constraints": None,
                "required": True,
                "display_order": 1,
            }
        ],
    }


@router.get("/{context_id}/options")
def context_options(context_id: int, session_id: int | None = None) -> dict:
    return {
        "context_id": context_id,
        "session_id": session_id,
        "option_sets": [{"value_type": "DRIVER", "items": [{"value": "ALO", "label": "Fernando Alonso"}]}],
    }


@router.get("/{context_id}/distribution")
def context_distribution(context_id: int, session_id: int, bet_score_id: int) -> dict:
    return {
        "context_id": context_id,
        "session_id": session_id,
        "bet_score_id": bet_score_id,
        "total_submitted": 22,
        "counts": [{"value": "ALO", "n": 4}, {"value": "VER", "n": 10}],
    }


@router.get("/{context_id}/powerups/targets")
def powerups_targets(context_id: int, session_id: int, powerup_code: str) -> dict:
    return {
        "context_id": context_id,
        "session_id": session_id,
        "powerup_code": powerup_code,
        "targets": [{"target_type": "USER", "user": {"id": 2, "username": "pepe"}}],
    }
