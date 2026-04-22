from pydantic import BaseModel, Field


class RunCreateRequest(BaseModel):
    testline: str = Field(min_length=1)
    robotcase_path: str = Field(min_length=1)


class RunCreateResponse(BaseModel):
    run_id: str
    status: str
    message: str


class RunListItem(BaseModel):
    run_id: str
    testline: str
    robotcase_path: str
    status: str
    message: str
    created_at: str
    updated_at: str


class RunListResponse(BaseModel):
    items: list[RunListItem]


class RunDetailResponse(BaseModel):
    run_id: str
    testline: str
    robotcase_path: str
    status: str
    message: str
    created_at: str
    updated_at: str

