from __future__ import annotations

import http.client
import ssl
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class HTTPResponse:
    status: int
    body: str
    headers: dict[str, str]


class HTTPStatusError(Exception):
    def __init__(self, status: int, body: str, headers: dict[str, str] | None = None) -> None:
        self.status = status
        self.body = body
        self.headers = headers or {}
        super().__init__(f"HTTP {status}")


class HTTPConnectionError(Exception):
    pass


class HTTPClient(Protocol):
    @property
    def name(self) -> str: ...

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes | None,
        open_timeout: float,
        read_timeout: float,
        write_timeout: float,
    ) -> HTTPResponse: ...


class UrllibHTTPClient:
    name = "urllib"

    def __init__(
        self,
        *,
        proxy: str | None = None,
        verify_ssl_certs: bool = True,
    ) -> None:
        self._proxy = proxy
        self._verify_ssl_certs = verify_ssl_certs

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes | None,
        open_timeout: float,
        read_timeout: float,
        write_timeout: float,
    ) -> HTTPResponse:
        if self._proxy is not None:
            return self._request_via_proxy(
                method,
                url,
                headers=headers,
                body=body,
                timeout=max(open_timeout, read_timeout, write_timeout),
            )
        return self._request_direct(
            method,
            url,
            headers=headers,
            body=body,
            open_timeout=open_timeout,
            read_timeout=read_timeout,
            write_timeout=write_timeout,
        )

    def _request_via_proxy(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes | None,
        timeout: float,
    ) -> HTTPResponse:
        proxy_map = {"http": self._proxy, "https": self._proxy}
        handlers: list[Any] = [urllib.request.ProxyHandler(proxy_map)]
        if not self._verify_ssl_certs:
            handlers.append(urllib.request.HTTPSHandler(context=ssl._create_unverified_context()))
        opener = urllib.request.build_opener(*handlers)
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with opener.open(req, timeout=timeout) as resp:
                response_body = resp.read().decode("utf-8")
                return HTTPResponse(
                    status=resp.status,
                    body=response_body,
                    headers=dict(resp.headers),
                )
        except urllib.error.HTTPError as exc:
            response_body = exc.read().decode("utf-8") if exc.fp else ""
            raise HTTPStatusError(
                exc.code,
                response_body,
                dict(exc.headers) if exc.headers else {},
            ) from exc
        except (TimeoutError, urllib.error.URLError, OSError) as exc:
            raise HTTPConnectionError(str(exc)) from exc

    def _request_direct(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes | None,
        open_timeout: float,
        read_timeout: float,
        write_timeout: float,
    ) -> HTTPResponse:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise HTTPConnectionError(f"Unsupported URL scheme: {parsed.scheme!r}")

        host = parsed.hostname
        if host is None:
            raise HTTPConnectionError(f"Invalid URL: {url!r}")

        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"

        conn: http.client.HTTPConnection
        if parsed.scheme == "https":
            context = (
                ssl.create_default_context()
                if self._verify_ssl_certs
                else ssl._create_unverified_context()
            )
            conn = http.client.HTTPSConnection(host, port, timeout=open_timeout, context=context)
        else:
            conn = http.client.HTTPConnection(host, port, timeout=open_timeout)

        try:
            conn.connect()
            if conn.sock is not None and body is not None:
                conn.sock.settimeout(write_timeout)
            conn.request(method, path, body=body, headers=headers)
            if conn.sock is not None:
                conn.sock.settimeout(read_timeout)
            raw = conn.getresponse()
            response_body = raw.read().decode("utf-8")
            resp_headers = dict(raw.getheaders())
            if raw.status >= 400:
                raise HTTPStatusError(raw.status, response_body, resp_headers)
            return HTTPResponse(status=raw.status, body=response_body, headers=resp_headers)
        except HTTPStatusError:
            raise
        except (TimeoutError, urllib.error.URLError, OSError, http.client.HTTPException) as exc:
            raise HTTPConnectionError(str(exc)) from exc
        finally:
            conn.close()


class HttpxHTTPClient:
    name = "httpx"

    def __init__(
        self,
        *,
        proxy: str | None = None,
        verify_ssl_certs: bool = True,
        client: Any = None,
    ) -> None:
        if client is not None:
            self._client = client
            self._owns_client = False
            return
        try:
            import httpx
        except ImportError as exc:
            raise ImportError(
                "httpx is required for HttpxHTTPClient. Install with: pip install clicksign[httpx]"
            ) from exc
        self._client = httpx.Client(
            proxy=proxy,
            verify=verify_ssl_certs,
        )
        self._owns_client = True

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes | None,
        open_timeout: float,
        read_timeout: float,
        write_timeout: float,
    ) -> HTTPResponse:
        if self._owns_client:
            import httpx

            timeout = httpx.Timeout(
                connect=open_timeout,
                read=read_timeout,
                write=write_timeout,
                pool=open_timeout,
            )
        else:
            timeout = max(open_timeout, read_timeout, write_timeout)

        try:
            response = self._client.request(
                method,
                url,
                headers=headers,
                content=body,
                timeout=timeout,
            )
        except Exception as exc:
            exc_name = type(exc).__name__
            if exc_name == "HTTPStatusError":
                raise HTTPStatusError(
                    exc.response.status_code,
                    exc.response.text,
                    dict(exc.response.headers),
                ) from exc
            if exc_name == "RequestError":
                raise HTTPConnectionError(str(exc)) from exc
            raise

        if response.status_code >= 400:
            raise HTTPStatusError(
                response.status_code,
                response.text,
                dict(response.headers),
            )
        return HTTPResponse(
            status=response.status_code,
            body=response.text,
            headers=dict(response.headers),
        )

    def __del__(self) -> None:
        if getattr(self, "_owns_client", False):
            self._client.close()


def default_http_client(
    *,
    proxy: str | None = None,
    verify_ssl_certs: bool = True,
) -> HTTPClient:
    return UrllibHTTPClient(proxy=proxy, verify_ssl_certs=verify_ssl_certs)


class AsyncHTTPClient(Protocol):
    @property
    def name(self) -> str: ...

    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes | None,
        open_timeout: float,
        read_timeout: float,
        write_timeout: float,
    ) -> HTTPResponse: ...

    async def aclose(self) -> None: ...


class HttpxAsyncHTTPClient:
    name = "httpx-async"

    def __init__(
        self,
        *,
        proxy: str | None = None,
        verify_ssl_certs: bool = True,
        client: Any = None,
    ) -> None:
        if client is not None:
            self._client = client
            self._owns_client = False
            return
        try:
            import httpx
        except ImportError as exc:
            raise ImportError(
                "httpx is required for async HTTP. Install with: pip install clicksign[async]"
            ) from exc
        self._client = httpx.AsyncClient(
            proxy=proxy,
            verify=verify_ssl_certs,
        )
        self._owns_client = True

    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes | None,
        open_timeout: float,
        read_timeout: float,
        write_timeout: float,
    ) -> HTTPResponse:
        if self._owns_client:
            import httpx

            timeout = httpx.Timeout(
                connect=open_timeout,
                read=read_timeout,
                write=write_timeout,
                pool=open_timeout,
            )
        else:
            timeout = max(open_timeout, read_timeout, write_timeout)

        try:
            response = await self._client.request(
                method,
                url,
                headers=headers,
                content=body,
                timeout=timeout,
            )
        except Exception as exc:
            exc_name = type(exc).__name__
            if exc_name == "HTTPStatusError":
                raise HTTPStatusError(
                    exc.response.status_code,
                    exc.response.text,
                    dict(exc.response.headers),
                ) from exc
            if exc_name == "RequestError":
                raise HTTPConnectionError(str(exc)) from exc
            raise

        if response.status_code >= 400:
            raise HTTPStatusError(
                response.status_code,
                response.text,
                dict(response.headers),
            )
        return HTTPResponse(
            status=response.status_code,
            body=response.text,
            headers=dict(response.headers),
        )

    async def aclose(self) -> None:
        if getattr(self, "_owns_client", False):
            await self._client.aclose()


def default_async_http_client(
    *,
    proxy: str | None = None,
    verify_ssl_certs: bool = True,
) -> AsyncHTTPClient:
    return HttpxAsyncHTTPClient(proxy=proxy, verify_ssl_certs=verify_ssl_certs)
