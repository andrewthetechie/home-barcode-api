from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Album(Base):
    __tablename__ = "albums"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    artist: Mapped[str] = mapped_column(index=True, unique=True)
    name: Mapped[str] = mapped_column(index=True, unique=True)
    spotify_id: Mapped[str] = mapped_column(index=True)
    discogs_id: Mapped[str] = mapped_column(unique=True)
    last_update: Mapped[datetime]
