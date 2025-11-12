from src.utils import TIME_ALLOWED_MODIFICATION
from src.utils.time import get_datetime, get_timezone


from datetime import (timedelta, datetime)




ALL = ['*']
ALLOWED = True

# máximo tamaño de archivo (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# extensiones permitidas para la carga de archivos
ALLOWED_FILE_EXTENSIONS = (
    'pdf', 'doc', 'docx',
    'xls', 'xlsx', 'xlsm',
    'csv', 'txt',
    'ppt', 'pptx', 'msg', 'png',
    'jpg', 'jpeg', 'zip', 'rar',
    '7z',
)


MEDIA_TYPE = 'application/json'






def get_modification_date_status(date: (datetime | str)) -> bool:
    current_date = get_datetime()
    current_date.replace(microsecond=0)

    # si hoy es día 3 o 4 de la semana (miércoles o jueves)
    # se agregan 48 horas adicionales al tiempo permitido de modificación
    time_allowed_modification = int(TIME_ALLOWED_MODIFICATION) + 48 if current_date.weekday() in [3, 4] else int(TIME_ALLOWED_MODIFICATION)

    # asegura que la fecha de creación tenga una zona horaria asignada.
    # si la fecha ya tiene tzinfo, esto puede lanzar un error.
    creation_date = get_timezone().localize(date)

    # calcula la fecha límite de modificación sumando las horas permitidas.
    modification_deadline = creation_date + timedelta(hours=time_allowed_modification)

    # si la fecha actual supera la fecha límite, la modificación no está permitida.
    return False if current_date > modification_deadline else True

