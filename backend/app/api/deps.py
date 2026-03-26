from collections.abc import Callable

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy import SqlAlchemyAccessRepository
from app.core.config import settings
from app.core.security import (
    ACCESS_TOKEN_COOKIE_NAME,
    get_access_token_subject,
)
from app.api.error_catalogs import ACCESS_ERROR_MAP, AUTH_ERROR_MAP
from app.api.error_translators import get_preferred_locale, translate_domain_error
from app.db.audit.context import set_audit_actor, set_audit_group
from app.db.auth import User
from app.db.session import get_db
from app.db.social import Group
from app.domain.access import (
    AccessError,
    EnsureGroupMember,
    EnsurePermissions,
    ResolveCurrentGroup,
    ResolveCurrentUser,
)
from app.domain.auth import AuthError


def _build_access_repository(db: Session) -> SqlAlchemyAccessRepository:
    return SqlAlchemyAccessRepository(db)


def _translate_access_error(exc: AccessError, *, locale: str | None) -> HTTPException:
    return translate_domain_error(exc, error_map=ACCESS_ERROR_MAP, locale=locale)

def _translate_auth_error(exc: AuthError, *, locale: str | None) -> HTTPException:
    return translate_domain_error(exc, error_map=AUTH_ERROR_MAP, locale=locale)






def _load_user_entity(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def _load_group_entity(db: Session, group_id: int) -> Group:
    group = db.get(Group, group_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return group


def _resolve_access_user(db: Session, subject: str | None):
    repository = _build_access_repository(db)
    use_case = ResolveCurrentUser(repository)
    return use_case.execute(subject)


def _resolve_access_group(db: Session, raw_group_id: str | None):
    repository = _build_access_repository(db)
    use_case = ResolveCurrentGroup(repository, default_group_id=settings.default_group_id)
    return use_case.execute(raw_group_id)


def _apply_user_audit_context(db: Session, request: Request | None, *, user_id: int, role: str | None) -> None:
    client_ip = request.client.host if request and request.client else None
    user_agent = request.headers.get("user-agent") if request else None
    set_audit_actor(db, user_id=user_id, role=role, ip=client_ip, user_agent=user_agent)


def _get_access_token_subject(request: Request | None) -> str:
    token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME) if request else None
    return get_access_token_subject(token)


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)
    try:
        subject = _get_access_token_subject(request)
    except AuthError as exc:
        raise _translate_auth_error(exc, locale=locale) from exc

    try:
        auth_user = _resolve_access_user(db, subject)
    except AccessError as exc:
        raise _translate_access_error(exc, locale=locale) from exc

    user = _load_user_entity(db, auth_user.id)
    _apply_user_audit_context(db, request, user_id=user.id, role=auth_user.role)
    return user


def get_current_group(
    request: Request,
    db: Session = Depends(get_db),
    x_group_id: str | None = Header(default=None),
) -> Group:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    try:
        group_ref = _resolve_access_group(db, x_group_id)
    except AccessError as exc:
        raise _translate_access_error(exc, locale=locale) from exc

    set_audit_group(db, group_id=group_ref.id)
    return _load_group_entity(db, group_ref.id)


def require_group_member(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    group: Group = Depends(get_current_group),
) -> tuple[User, Group]:
    repository = _build_access_repository(db)
    ensure_membership = EnsureGroupMember(repository)
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    try:
        auth_user = _resolve_access_user(db, str(user.id))
        auth_group = _resolve_access_group(db, str(group.id))
        ensure_membership.execute(auth_user, auth_group)
    except AccessError as exc:
        raise _translate_access_error(exc, locale=locale) from exc

    return user, group


def require_permissions_all(*required: str) -> Callable[..., User]:
    def dependency(
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
    ) -> User:
        ensure_permissions = EnsurePermissions()
        locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

        try:
            auth_user = _resolve_access_user(db, str(user.id))
            ensure_permissions.execute_all(auth_user, required)
        except AccessError as exc:
            raise _translate_access_error(exc, locale=locale) from exc

        return user

    return dependency


def require_permissions_any(*required: str) -> Callable[..., User]:
    def dependency(
        request: Request,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
    ) -> User:
        ensure_permissions = EnsurePermissions()
        locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

        try:
            auth_user = _resolve_access_user(db, str(user.id))
            ensure_permissions.execute_any(auth_user, required)
        except AccessError as exc:
            raise _translate_access_error(exc, locale=locale) from exc

        return user

    return dependency
