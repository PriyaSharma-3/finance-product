from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import dotenv_values

##  Initialize environment variables
config = dotenv_values(".env")


SQLALCHEMY_DATABASE_URL = f'postgresql://{config['USERNAME']}:{config['PASSWORD']}@{config['HOSTNAME']}:{config['PORT']}/{config['DBNAME']}'


engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()