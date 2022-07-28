# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.base_class import Base  # noqa
from app.models.tbl_model import tbl_model  # noqa
from app.models.tbl_user import tbl_user  # noqa
