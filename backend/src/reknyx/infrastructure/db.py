from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def build_database(settings):
    engine = create_engine(settings.database_url, pool_pre_ping=True, connect_args={"connect_timeout": 3})
    return engine, sessionmaker(engine, expire_on_commit=False)
