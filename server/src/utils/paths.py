from pathlib import Path

def create_directory(directories: list[Path]):
    for directory in directories:
        if not directory.exists():
            directory.mkdir()



CWD = Path(__file__).resolve().parent.parent.parent
SRC_DIRECTORY_PATH = Path(CWD / 'src')

STATIC_DIRECTORY_PATH = Path(SRC_DIRECTORY_PATH / 'static')
STORAGE_DIRECTORY_PATH = Path(SRC_DIRECTORY_PATH / 'storage')
LOG_DIRECTORY_PATH = Path(STATIC_DIRECTORY_PATH / 'logs')
UPLOADS_DIRECTORY_PATH = Path(STATIC_DIRECTORY_PATH / 'uploads')
PROFILE_PHOTOS_DIRECTORY_PATH = Path(UPLOADS_DIRECTORY_PATH / 'profiles')
POSTS_MEDIA_DIRECTORY_PATH = Path(UPLOADS_DIRECTORY_PATH / 'posts')
TICKETS_ATTACHMENTS_DIRECTORY_PATH = Path(UPLOADS_DIRECTORY_PATH / 'tickets')



create_directory(
    [
        STATIC_DIRECTORY_PATH,
        STORAGE_DIRECTORY_PATH,
        UPLOADS_DIRECTORY_PATH,
        PROFILE_PHOTOS_DIRECTORY_PATH,
        POSTS_MEDIA_DIRECTORY_PATH,
        TICKETS_ATTACHMENTS_DIRECTORY_PATH,
        LOG_DIRECTORY_PATH
    ]
)

LOG_FILE_NAME = 'events.log'
LOG_FILE_PATH = Path(LOG_DIRECTORY_PATH / LOG_FILE_NAME)
