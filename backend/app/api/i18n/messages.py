DEFAULT_LOCALE = "en"

MESSAGES = {
    "en": {
        "access.missing_subject": "Missing subject",
        "access.invalid_subject": "Invalid subject",
        "access.user_not_found": "User not found",
        "access.invalid_group_id": "Invalid X-Group-Id",
        "access.group_not_found": "Group not found",
        "access.not_group_member": "You are not authorized to access this group",
        "access.missing_permissions": "You are not authorized to perform this action",

        ##########################################################
        # ********              Auth Errors             ******** #                   
        ##########################################################

        "auth.invalid_credentials": "Invalid credentials",
        "auth.inactive_user": "This account cannot use password login",
        "auth.missing_access_token": "Missing access token",
        "auth.invalid_access_token": "Invalid access token",
        "auth.missing_refresh_token": "Missing refresh token",
        "auth.invalid_refresh_token": "Invalid refresh token",
        "auth.missing_refresh_subject": "Missing refresh subject",
        "auth.user_already_exists": "A user with this data already exists",
        "auth.invalid_google_token": "Invalid Google token",
        "auth.google_email_not_verified": "Google email is not verified",
        "auth.google_account_not_registered": "No Google account is registered with this identity",
        "auth.invalid_password_reset_token": "Invalid or expired password reset token",

        ##########################################################
        # ********              Auth Errors             ******** #                   
        ##########################################################

        "admin.season_already_exists": "Season {year} already exists",
        "admin.active_season_already_exists": "There is already an active season ({active_year})",
        "admin.country_already_exists": "Country {iso2} already exists",
        "admin.circuit_already_exists": "Circuit {code} already exists",
        "admin.country_not_found_for_circuit": "Country {country_iso2} was not found",
        "admin.season_not_found_for_testing_event": "Season '{season_year}' was not found.",
        "admin.circuit_not_found_for_testing_event": "Circuit '{circuit_code}' was not found.",
        "admin.testing_event_already_exists": "Testing event '{name}' already exists for season {season_year}.",
        "admin.duplicate_testing_event_session_order": "Session order '{session_order}' is duplicated.",
        "admin.testing_event_not_found": "Testing event '{testing_event_id}' was not found.",
        "admin.season_not_found_for_race_event": "Season '{season_year}' was not found.",
        "admin.circuit_not_found_for_race_event": "Circuit '{circuit_code}' was not found.",
        "admin.race_event_already_exists": "Race event for round {round_number} already exists in season {season_year}.",
        "admin.duplicate_race_event_session_type": "Session type '{session_type}' is duplicated.",
        "admin.race_event_not_found": "Race event '{race_event_id}' was not found.",


        "errors.unhandled": "An unexpected error occurred",
    },
    "es": {
        "access.missing_subject": "Falta el subject",
        "access.invalid_subject": "El subject no es valido",
        "access.user_not_found": "Usuario no encontrado",
        "access.invalid_group_id": "El X-Group-Id no es valido",
        "access.group_not_found": "Grupo no encontrado",
        "access.not_group_member": "No tienes permiso para acceder a este grupo",
        "access.missing_permissions": "No tienes permiso para realizar esta accion",

        ##########################################################
        # ********              Auth Errors             ******** #                   
        ##########################################################

        "auth.invalid_credentials": "Credenciales invalidas",
        "auth.inactive_user": "Esta cuenta no puede usar inicio de sesion por contrasena",
        "auth.missing_access_token": "Falta el token de acceso",
        "auth.invalid_access_token": "El token de acceso no es valido",
        "auth.missing_refresh_token": "Falta el token de refresh",
        "auth.invalid_refresh_token": "El token de refresh no es valido",
        "auth.missing_refresh_subject": "Falta el subject del refresh",
        "auth.user_already_exists": "Ya existe un usuario con estos datos",
        "auth.invalid_google_token": "El token de Google no es valido",
        "auth.google_email_not_verified": "El email de Google no esta verificado",
        "auth.google_account_not_registered": "No hay una cuenta de Google registrada con esta identidad",
        "auth.invalid_password_reset_token": "El token de restablecimiento no es valido o ha expirado",

        ##########################################################
        # ********              Auth Errors             ******** #                   
        ##########################################################

        "admin.season_already_exists": "La temporada {year} ya existe",
        "admin.active_season_already_exists": "Ya existe una temporada activa({active_year})",
        "admin.country_already_exists": "El pais {iso2} ya existe",
        "admin.circuit_already_exists": "El circuito {code} ya existe",
        "admin.country_not_found_for_circuit": "No se ha encontrado el pais {country_iso2}",
        "admin.season_not_found_for_testing_event": "No se ha encontrado la temporada '{season_year}'.",
        "admin.circuit_not_found_for_testing_event": "No se ha encontrado el circuito '{circuit_code}'.",
        "admin.testing_event_already_exists": "Testing event '{name}' ya existe para la sesion {season_year}.",
        "admin.duplicate_testing_event_session_order": "El orden de sesión '{session_order}' está duplicado.",
        "admin.season_not_found_for_race_event": "No se ha encontrado la temporada '{season_year}'.",
        "admin.circuit_not_found_for_race_event": "No se ha encontrado el circuito '{circuit_code}'.",
        "admin.race_event_already_exists": "Ya existe un race event para la ronda {round_number} de la temporada {season_year}.",
        "admin.duplicate_race_event_session_type": "El tipo de sesión '{session_type}' está duplicado.",

        "errors.unhandled": "Ha ocurrido un error inesperado",
    },
}


def resolve_message(error_code: str, locale: str | None) -> str:
    normalized_locale = (locale or DEFAULT_LOCALE).split(",")[0].split("-")[0].lower()
    messages = MESSAGES.get(normalized_locale) or MESSAGES[DEFAULT_LOCALE]
    return messages.get(error_code) or MESSAGES[DEFAULT_LOCALE].get(error_code, error_code)


def render_message(error_code: str, locale: str | None, public_params: dict | None = None) -> str:
    template = resolve_message(error_code, locale)
    if not public_params:
        return template

    try:
        return template.format(**public_params)
    except KeyError:
        return template
