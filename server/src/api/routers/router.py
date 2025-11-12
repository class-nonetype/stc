from src.utils import API_PREFIX
from src.api.routers.versions.v2 import (
    authentication,
    application,
    admin,
)

from fastapi import APIRouter


API_ROUTERS = {
    'admin' : [admin.router],
    'application' : [application.router],
    'authentication': [authentication.router]
}


router = APIRouter()

for key, values in API_ROUTERS.items():
    for value in values:
        router.include_router(router=value, prefix=API_PREFIX[key])
