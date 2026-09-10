from __future__ import annotations

import logging

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


logger = logging.getLogger(__name__)
WRITE_METHODS = {"POST", "PUT", "PATCH"}


class Utf8WriteValidationMiddleware:
    """Reject malformed UTF-8 JSON bodies before API validation or persistence."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] not in WRITE_METHODS:
            await self.app(scope, receive, send)
            return

        headers = {key.decode("latin-1").lower(): value.decode("latin-1") for key, value in scope["headers"]}
        content_type = headers.get("content-type", "").lower()
        if "application/json" not in content_type:
            await self.app(scope, receive, send)
            return

        messages, body = await self._read_body(receive)
        try:
            body.decode("utf-8", "strict")
        except UnicodeDecodeError:
            logger.warning("UTF-8 validation failed for %s: malformed JSON body", scope["path"])
            response = JSONResponse(
                status_code=400,
                content={"detail": "Request body must contain valid UTF-8 text."},
            )
            await response(scope, receive, send)
            return

        await self.app(scope, self._replay_body(messages), send)

    @staticmethod
    async def _read_body(receive: Receive) -> tuple[list[Message], bytes]:
        messages: list[Message] = []
        chunks: list[bytes] = []
        while True:
            message = await receive()
            messages.append(message)
            if message["type"] != "http.request":
                break
            chunks.append(message.get("body", b""))
            if not message.get("more_body", False):
                break
        return messages, b"".join(chunks)

    @staticmethod
    def _replay_body(messages: list[Message]) -> Receive:
        remaining = iter(messages)

        async def receive() -> Message:
            try:
                return next(remaining)
            except StopIteration:
                return {"type": "http.disconnect"}

        return receive