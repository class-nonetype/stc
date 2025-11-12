import time
import uuid

from logging import (
    config,
    Formatter,
    FileHandler,
    Filter,
    LogRecord,
    getLogger,
    DEBUG,
)

Formatter.converter = time.gmtime

from src.utils.paths import LOG_FILE_PATH
from src.utils.formats import LOG_FORMATTER


logger = getLogger(__name__)
logger.setLevel(DEBUG)

with open(file=LOG_FILE_PATH, mode='w') as log_file:
    pass


def log_handler():
    LOG_FILE_HANDLER = FileHandler(filename=LOG_FILE_PATH, mode='+a', encoding='utf-8')
    LOG_FILE_HANDLER.setFormatter(fmt=LOG_FORMATTER)

    logger.addHandler(LOG_FILE_HANDLER)

def log_filter():
    class FilterSensitiveHeaders(Filter):
        def filter(self, record: LogRecord) -> bool:

            if isinstance(record.msg, str):
                if record.args:
                    new_arguments = []
                    for argument in record.args:
                        if isinstance(argument, str) and 'Authorization' in argument:
                            argument = argument.split('Authorization')
                            argument = '%s: <hidden>' % argument[0]
                            argument = argument.replace(argument[0], argument[0])
                        
                        if isinstance(argument, str):
                            for section in argument.split('/'):
                                try:
                                    section = uuid.UUID(section)
                                    argument = argument.replace(str(section), '<hidden>')
                                except ValueError:
                                    pass

                        new_arguments.append(argument)

                    record.args = tuple(new_arguments)

                if 'Authorization' in record.msg:
                    record.msg = record.msg.split('Authorization')
                    record.msg = '%s: <hidden>' % record.msg[0]
                    record.msg = record.msg.replace(record.msg[0], record.msg[0])
                    print(f'{__file__} ::: {record.msg}')

            return True


    from uvicorn.config import LOGGING_CONFIG

    LOGGING_CONFIG['filters'] = {
        'filter_sensitive_headers': {
            '()': FilterSensitiveHeaders,
        }
    }

    LOGGING_CONFIG['loggers']['uvicorn.access']['filters'] = ['filter_sensitive_headers']

    config.dictConfig(LOGGING_CONFIG)

    getLogger('uvicorn.access').addFilter(FilterSensitiveHeaders())



log_handler()
log_filter()

