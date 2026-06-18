import json
from enum import Enum
from typing import Any

from aiohttp import ClientError

from async_tls.utils.structures import CaseInsensitiveDict
from .cookies import cookiejar_from_dict


class Protocol(Enum):
    HTTP_1_1 = "HTTP/1.1"
    HTTP_2 = "HTTP/2.0"
    HTTP_3 = "HTTP/3.0"

    @classmethod
    def from_string(cls, value: str) -> "Protocol | None":
        if not value:
            return None
        for member in cls:
            if member.value == value:
                return member
        return None


class Response:

    def __init__(self):
        self.url: str | None = None
        self.status_code: int | None = None
        self.text: str | None = None
        self.headers: CaseInsensitiveDict = CaseInsensitiveDict()
        self.cookies = cookiejar_from_dict({})
        self._content: bytes | None = None
        self._content_consumed: bool = False
        self.history = []
        self.used_protocol: Protocol | None = None

    def __enter__(self):
        return self

    def __repr__(self):
        return f"<Response [{self.status_code}]>"

    def json(self, **kwargs) -> dict | list:
        return json.loads(self.text, **kwargs)

    def raise_for_status(self):
        if 400 <= self.status_code < 500:
            raise ClientError(f'Client Error: {self.status_code} for url: {self.url}')
        elif 500 <= self.status_code < 600:
            raise ClientError(f'Server Error: {self.status_code} for url: {self.url}')

    @property
    def content(self) -> bytes:
        if self._content is None:
            if self._content_consumed:
                raise RuntimeError("The content for this response was already consumed.")
            self._content = self.text.encode() if self.status_code != 0 else b""
            self._content_consumed = True
        return self._content


def build_response(res: dict[str, Any], res_cookies) -> Response:
    response = Response()
    response.url = res.get("target")
    response.status_code = res.get("status", 0)
    response.text = res.get("body", "")

    response_headers = CaseInsensitiveDict()
    for key, value in res.get("headers", {}).items():
        response_headers[key] = value[0] if len(value) == 1 else value
    response.headers = response_headers

    response.cookies = res_cookies
    response.used_protocol = Protocol.from_string(res.get("usedProtocol"))
    return response