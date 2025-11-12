from sqlalchemy import create_engine
from src.utils import DATABASE_URL
from src.core.database.base import Base
from src.core.database.models import *

engine = create_engine(DATABASE_URL, future=True)
#Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
