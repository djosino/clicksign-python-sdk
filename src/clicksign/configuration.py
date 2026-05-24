from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ._http.transport import HTTPClient

_ENVIRONMENTS = {
    "production": "https://app.clicksign.com/api/v3",
    "sandbox": "https://sandbox.clicksign.com/api/v3",
}

DEFAULT_MAX_RETRIES = 3


class Configuration:
    def __init__(self) -> None:
        self.api_key: str | None = None
        self.base_url: str = _ENVIRONMENTS["production"]
        self.open_timeout: float = 2.0
        self.read_timeout: float = 10.0
        self.write_timeout: float = 10.0
        self.max_retries: int = DEFAULT_MAX_RETRIES
        self.logger: Any = None
        self.proxy: str | None = None
        self.verify_ssl_certs: bool = True
        self.http_client: HTTPClient | None = None
        self.enable_telemetry: bool = False
        self.telemetry_url: str | None = None
        self.log_level: str | None = None

    @property
    def environment(self) -> str | None:
        for env, url in _ENVIRONMENTS.items():
            if self.base_url == url:
                return env
        return None

    @environment.setter
    def environment(self, value: str) -> None:
        """Set ``base_url`` by environment name.

        Valid values: ``"production"``, ``"sandbox"``. Raises :class:`ValueError`
        for unknown names. Side effect: updates ``self.base_url``.
        """
        env_str = str(value)
        if env_str not in _ENVIRONMENTS:
            raise ValueError(f"Unknown environment: {value!r}. Must be 'production' or 'sandbox'.")
        self.base_url = _ENVIRONMENTS[env_str]
