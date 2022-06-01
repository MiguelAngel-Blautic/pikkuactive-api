from typing import List

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import Model
from app.models.movement import Movement
from app.schemas.movement import MovementCreate, MovementUpdate


class CRUDMovement(CRUDBase[Movement, MovementCreate, MovementUpdate]):
    def create_with_owner(
            self, db: Session, *, obj_in: MovementCreate, owner_id: int
    ) -> Movement:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, owner_id=owner_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_all_by_owner(
            self, db: Session, models: List[Model], skip: int = 0, limit: int = 100
    ) -> List[Movement]:
        ids = [model.id for model in models]
        return (
            db.query(self.model)
                .filter(Movement.owner_id.in_(ids))
                .offset(skip)
                .limit(limit)
                .all()
        )


movement = CRUDMovement(Movement)
