
if __name__ == '__main__':
    from src.api.application import get_application
    from uvicorn import run

    run(
        app=get_application(),
        host='localhost',
        port=8000
    )
