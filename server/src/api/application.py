from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.utils.properties import (API_TITLE, API_DESCRIPTION, API_VERSION, API_PREFIX)
from src.utils.controls import (ALL, ALLOWED)
from src.utils.paths import (STATIC_DIRECTORY_PATH, UPLOADS_DIRECTORY_PATH)
from src.api.routers.router import router



def get_application() -> FastAPI:
    application = FastAPI(
        title=API_TITLE,
        description=API_DESCRIPTION,
        version=API_VERSION,
    )
    application.include_router(router=router)

    if STATIC_DIRECTORY_PATH.exists():
        application.mount(
            path=API_PREFIX['static'],
            app=StaticFiles(directory=UPLOADS_DIRECTORY_PATH),
            name='static'
        )

    application.add_middleware(
        middleware_class=CORSMiddleware,
        allow_origins=ALL,
        allow_credentials=ALLOWED,
        allow_methods=ALL,
        allow_headers=ALL
    )

    return application
