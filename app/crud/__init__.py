from .crud_model import model
from .crud_user import user
from .crud_movement import movement
from .crud_capture import capture

# For a new basic set of CRUD operations you could just do

from .base import CRUDBase
from app.models.tbl_position import tbl_position
from app.models.tbl_grupo_negativo import tbl_grupo_negativo
from app.schemas.position import PositionCreate, PositionUpdate
from app.schemas.grupo import GrupoCreate, GrupoUpdate

# item = CRUDBase[Item, ItemCreate, ItemUpdate](Item)

position = CRUDBase[tbl_position, PositionCreate, PositionUpdate](tbl_position)
grupo = CRUDBase[tbl_grupo_negativo, GrupoCreate, GrupoUpdate](tbl_grupo_negativo)
