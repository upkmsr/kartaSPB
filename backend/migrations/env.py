from alembic import context

from app.database import get_engine

if context.is_offline_mode():
    context.configure(url="postgresql+psycopg://", literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    with get_engine().connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()
