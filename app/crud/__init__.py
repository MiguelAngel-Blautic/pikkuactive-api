from .crud_model import model
from .crud_sesion import sesion
from .crud_user import user
from .crud_movement import movement
from .crud_capture import capture
from .crud_asignado import asignado
from .crud_ejercicio import ejercicio
from .crud_umbral import umbral
from .crud_resultado import resultado
from .crud_entrena import entrena

# For a new basic set of CRUD operations you could just do

from .base import CRUDBase
from app.models.tbl_position import tbl_position
from app.schemas.position import PositionCreate, PositionUpdate

# item = CRUDBase[Item, ItemCreate, ItemUpdate](Item)
position = CRUDBase[tbl_position, PositionCreate, PositionUpdate](tbl_position)
