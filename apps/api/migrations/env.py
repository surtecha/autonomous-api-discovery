from alembic import context
from sqlalchemy import create_engine

from apps.api.database import Base
from apps.api.settings import Settings

engine = create_engine(Settings().database_url.get_secret_value(), hide_parameters=True)
with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()
