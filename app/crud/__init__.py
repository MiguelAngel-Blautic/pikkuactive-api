from .crud_model import model
from .crud_user import user
from .crud_movement import movement
from .crud_capture import capture

# For a new basic set of CRUD operations you could just do

from .base import CRUDBase
from app.models.position import Position
from app.schemas.position import PositionCreate, PositionUpdate

# item = CRUDBase[Item, ItemCreate, ItemUpdate](Item)
position = CRUDBase[Position, PositionCreate, PositionUpdate](Position)
