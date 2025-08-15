from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app import schemas, crud, kafka
from app.database import get_db

router = APIRouter()

@router.post("/produce/")
async def produce(message: schemas.Message):
    try:
        kafka.produce_message(message.content)
        return {"status": "sent", "content": message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/consumed_messages/", response_model=List[str])
async def consumed_messages():
    return kafka.consumed_messages

@router.get("/users/", response_model=List[schemas.UserInDB])
async def read_users(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    users = await crud.get_users(db, skip, limit)
    return users

@router.post("/users/", response_model=schemas.UserInDB)
async def create_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await crud.create_user(db, user)
    return db_user

@router.get("/users/{user_id}", response_model=schemas.UserInDB)
async def read_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/users/{user_id}", response_model=schemas.UserInDB)
async def update_user(user_id: int, user_update: schemas.UserUpdate, db: AsyncSession = Depends(get_db)):
    db_user = await crud.get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    updated_user = await crud.update_user(db, db_user, user_update)
    return updated_user

@router.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    db_user = await crud.get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    await crud.delete_user(db, db_user)