from os import getenv
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = getenv('SECRET_KEY', None)
DATABASE_URL = getenv('DATABASE_URL', None)
TZ = getenv('TZ', None)
TIME_ALLOWED_MODIFICATION = getenv('TIME_ALLOWED_MODIFICATION', None)


from src.utils.controls import *
from src.utils.formats import *
from src.utils.generators import *
from src.utils.logger import *
from src.utils.paths import *
from src.utils.properties import *
from src.utils.time import *
