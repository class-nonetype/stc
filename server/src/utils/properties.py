from src.utils.time import get_timezone

API_TITLE = 'Backend'
API_DESCRIPTION = '-'
API_VERSION = 'v2'
API_HOST = '0.0.0.0'
API_PORT = 7500
API_TIMEZONE = get_timezone()

API_PREFIX = {
    'static'            : f'/api/{API_VERSION}/static',
    'application'       : f'/api/{API_VERSION}/application',
    'authentication'    : f'/api/{API_VERSION}/authentication',
    'admin'             : f'/api/{API_VERSION}/admin',
}


DATABASE_DRIVERS = {
    'postgresql': 'postgresql+asyncpg',
    'mysql': 'mysql+aiomysql',
    'mariadb': 'mariadb+aiomysql',
    'sqlite': 'sqlite+aiosqlite',
}


