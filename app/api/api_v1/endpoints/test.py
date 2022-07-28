from typing import Any, List
import sqlalchemy as db
from fastapi import APIRouter, Body, Depends, HTTPException

router = APIRouter()


@router.get("/", response_model=str)
def test(
        id: int,
) -> Any:
    engine = db.create_engine('mariadb+mariadbconnector://root:$Sqnon2022!@82.223.19.236:3306/ziven-active')
    connection = engine.connect()
    metadata = db.MetaData()
    user = db.Table('tblUser', metadata, autoload=True, autoload_with=engine)
    query = db.select([user.columns.fldSFullName]).where(user.columns.id == id)
    res = connection.execute(query).first()
    print(res[0])
    return res[0]
