from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Token(Base):
    __tablename__ = "tokens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    hashed_token: Mapped[str]
    notes: Mapped[str]
