from pydantic import BaseModel, Field

class RunCreateRequest(BaseModel):
    testline: str = Field(min_length=1)
    robotcase_path: str = Field(min_length=1)


class RunCreateResponse(BaseModel):
    run_id: str
    status: str
    message: str

