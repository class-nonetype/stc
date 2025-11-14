from __future__ import annotations

from uuid import UUID
from fastapi import Response
from fastapi.responses import (
  JSONResponse,
  FileResponse,
  StreamingResponse
)


def _stringify_uuids(obj):
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, list):
        return [_stringify_uuids(item) for item in obj]
    if isinstance(obj, tuple):
        return tuple(_stringify_uuids(item) for item in obj)
    if isinstance(obj, dict):
        return {key: _stringify_uuids(value) for key, value in obj.items()}
    return obj


def response(response_type: int, **kwargs) -> (Response | JSONResponse | StreamingResponse | FileResponse | None):
    if 'content' in kwargs:
        kwargs = kwargs.copy()
        kwargs['content'] = _stringify_uuids(kwargs['content'])

    match response_type:
      case 1: return Response(**kwargs)
      case 2: return JSONResponse(**kwargs)
      case 3: return StreamingResponse(**kwargs)
      case 4: return FileResponse(**kwargs)
      case _: return None
