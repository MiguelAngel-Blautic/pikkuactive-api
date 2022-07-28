from sqlalchemy.orm import Session

from app import crud
from app.schemas.model import ModelCreate, ModelUpdate
from app.tests.utils.user import create_random_user
from app.tests.utils.utils import random_lower_string


def test_create_item(db: Session) -> None:
    title = random_lower_string()
    description = random_lower_string()
    item_in = ModelCreate(title=title, description=description)
    user = create_random_user(db)
    item = crud.model.create_with_owner(db=db, obj_in=item_in, owner_id=user.id)
    assert item.title == title
    assert item.fldSDescription == description
    assert item.fkOwner == user.id


def test_get_item(db: Session) -> None:
    title = random_lower_string()
    description = random_lower_string()
    item_in = ModelCreate(title=title, description=description)
    user = create_random_user(db)
    item = crud.model.create_with_owner(db=db, obj_in=item_in, owner_id=user.id)
    stored_item = crud.model.get(db=db, id=item.id)
    assert stored_item
    assert item.id == stored_item.id
    assert item.title == stored_item.title
    assert item.fldSDescription == stored_item.fldSDescription
    assert item.fkOwner == stored_item.fkOwner


def test_update_item(db: Session) -> None:
    title = random_lower_string()
    description = random_lower_string()
    item_in = ModelCreate(title=title, description=description)
    user = create_random_user(db)
    item = crud.model.create_with_owner(db=db, obj_in=item_in, owner_id=user.id)
    description2 = random_lower_string()
    item_update = ModelUpdate(description=description2)
    item2 = crud.model.update(db=db, db_obj=item, obj_in=item_update)
    assert item.id == item2.id
    assert item.title == item2.title
    assert item2.fldSDescription == description2
    assert item.fkOwner == item2.fkOwner


def test_delete_item(db: Session) -> None:
    title = random_lower_string()
    description = random_lower_string()
    item_in = ModelCreate(title=title, description=description)
    user = create_random_user(db)
    item = crud.model.create_with_owner(db=db, obj_in=item_in, owner_id=user.id)
    item2 = crud.model.remove(db=db, id=item.id)
    item3 = crud.model.get(db=db, id=item.id)
    assert item3 is None
    assert item2.id == item.id
    assert item2.title == title
    assert item2.fldSDescription == description
    assert item2.fkOwner == user.id
