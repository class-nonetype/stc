from datetime import datetime, timedelta
from typing import Set

import jwt
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.utils import SECRET_KEY
from src.utils.time import get_datetime

from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN


REVOKED_ACCESS_TOKENS: Set[str] = set()

def set_expiration_date(hours: int) -> str:
    expiration_date = get_datetime() + timedelta(hours=hours)
    return expiration_date.strftime('%Y-%m-%d %H:%M:%S.%f%z')


async def create_access_token(credential: dict) -> str:
    return jwt.encode(
        payload={**credential, 'expires': set_expiration_date(hours=8)},
        key=SECRET_KEY,
        algorithm='HS256'
    )


def revoke_access_token(token: str) -> None:
    if token:
        REVOKED_ACCESS_TOKENS.add(token)


def is_access_token_revoked(token: str) -> bool:
    return token in REVOKED_ACCESS_TOKENS


def verify_access_token(token: str, output: bool = False):
    try:
        if is_access_token_revoked(token):
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail='Revoked token.')

        decoded_token = jwt.decode(jwt=token, key=SECRET_KEY, algorithms=['HS256'])
        expiration_date = datetime.strptime(decoded_token['expires'], '%Y-%m-%d %H:%M:%S.%f%z')
        current_date = get_datetime()

        if (output and expiration_date < current_date):
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail='Expired token.')

        return decoded_token

    except jwt.exceptions.DecodeError:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail='Invalid token.')


def decode_access_token(token: str) -> dict:
    try:
        if is_access_token_revoked(token):
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail='Revoked token.')

        decoded_token = jwt.decode(jwt=token, key=SECRET_KEY, algorithms=['HS256'])
        expiration_date = datetime.strptime(decoded_token['expires'], '%Y-%m-%d %H:%M:%S.%f%z')
        current_date = datetime.now(expiration_date.tzinfo)

        if (expiration_date > current_date):
            return decoded_token

    except jwt.exceptions.DecodeError:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail='Invalid token.')



class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)


    async def __call__(self, request: Request):
        credential: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)

        if not credential:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail='Invalid authorization.')

        if not credential.scheme == 'Bearer':
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail='Invalid authorization\'s schema.')
        
        if not self.validate_jwt(credential.credentials):
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail='Invalid or expired token.')
        
        return credential.credentials


    def validate_jwt(self, token: str) -> bool:
        token_validity = False

        try:
            payload = decode_access_token(token)

        except:
            payload = None

        if payload:
            token_validity = True

        return token_validity
