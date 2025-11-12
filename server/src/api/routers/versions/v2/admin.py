from fastapi import (
    APIRouter,
    Request,
    Depends
)
from fastapi.encoders import jsonable_encoder

from src.api.responses import response
from src.utils.controls import MEDIA_TYPE
from src.core.database.session import database
from src.utils.logger import logger

from starlette.status import *

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

router = APIRouter()



'''@router.get(path='/user-roles')
async def get_all_user_roles(session: AsyncSession = Depends(database)):
    response_type = 2
    content = await select_all_user_roles(session=session)
    json_content = jsonable_encoder(
      obj={'status': 'success', 'data' : content} if content else {'status': 'error', 'data' : None}
    )

    status_code = HTTP_200_OK if content else HTTP_404_NOT_FOUND

    return response(
        response_type=response_type,
        status_code=status_code,
        media_type=MEDIA_TYPE,
        content=json_content
    )
'''
