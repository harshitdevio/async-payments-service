from sqlalchemy.orm import declarative_base, DeclarativeMeta

class BaseModel:
    pass


Base: DeclarativeMeta = declarative_base(cls=BaseModel)
