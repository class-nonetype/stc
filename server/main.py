
if __name__ == '__main__':
    from src.api.application import get_application
    from uvicorn import run

    run(
        app=get_application(),
        #host='0.0.0.0',
        host='localhost',
        port=8000
    )
