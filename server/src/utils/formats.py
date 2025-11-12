from logging import Formatter

LOG_MESSAGE_FORMAT = '%(asctime)-10s %(levelname)-10s %(filename)-10s -> %(funcName)s::%(lineno)s: %(message)s'
LOG_DATE_FORMAT = '%d/%m/%Y %I:%M:%S %p'

LOG_FORMATTER = Formatter(fmt=LOG_MESSAGE_FORMAT, datefmt=LOG_DATE_FORMAT, style='%')


FILE_SIZE_FORMAT = '{:.2f} MB'
