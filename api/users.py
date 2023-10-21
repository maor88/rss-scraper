from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db import get_user_by_email
from messages import AuthResponse

router = APIRouter()


class UserLogin(BaseModel):
    email: str


@router.post("/", response_model=dict)
async def login(user_login: UserLogin):
    user = get_user_by_email(user_login.email)
    if user is None:
        raise HTTPException(status_code=404, detail=AuthResponse.user_not_exist(user_login.email))
    else:
        response_model = dict()
        response_model["access_token"] = user.token
        response_model["token_type"] = "bearer"
        return response_model
