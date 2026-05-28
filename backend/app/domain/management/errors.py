class ManagementError(Exception):
    @property
    def context(self) -> dict:
        return {}

    @property
    def public_params(self) -> dict:
        return {}

    @property
    def log_level(self) -> str:
        return "warning"

