"""
RSS scraper app - sendCloud

auth login using to generate validate and retrieve user token

Author: Maor Avitan
"""


import jwt

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette import status

ALGORITHM = "HS256"
SECRET_KEY = "f5537643e12e73b516ba1dda92e91888"


def create_token(data: dict):
    token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    return token


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Function to get the current active user from the token
def get_user_id(payload: dict):
    try:
        user_id: int = payload.get("id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        token_data = TokenData(user_id=user_id)
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    return token_data.user_id


# Function to validate the token
def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return get_user_id(payload)


class TokenData:
    def __init__(self, user_id: int):
        self.user_id = user_id

