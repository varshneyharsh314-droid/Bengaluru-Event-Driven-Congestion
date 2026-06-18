# Import all the models, so that Base has them before being
# imported by Alembic or the app creation hook.
from app.core.database import Base  # noqa
