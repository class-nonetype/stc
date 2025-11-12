from fastapi import (
    APIRouter,
    Request,
    Response,
    Depends,
    HTTPException,
    security
)
from src.utils.controls import MEDIA_TYPE
from src.api.responses import response

router = APIRouter()
authentication_schema = security.HTTPBearer()
