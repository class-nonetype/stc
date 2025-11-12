from fastapi import Response
from fastapi.responses import (JSONResponse, StreamingResponse)

def response(response_type: int, **kwargs) -> (Response | JSONResponse | StreamingResponse | None):
    match response_type:
      case 1: return Response(**kwargs)
      case 2: return JSONResponse(**kwargs)
      case 3: return StreamingResponse(**kwargs)
      case _: return None
