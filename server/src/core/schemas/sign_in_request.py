from pydantic import BaseModel, ConfigDict

class SignInRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    password: str
