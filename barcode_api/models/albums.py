from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class CacheTable(Base):
    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    barcode: Mapped[str] = mapped_column(index=True, unique=True)
    last_update: Mapped[datetime] = mapped_column(onupdate=func.now(), default=func.now())
    is_deleted: Mapped[bool] = mapped_column(default=False)


class Album(CacheTable):
    __tablename__ = "albums"

    artist: Mapped[str] = mapped_column(index=True)
    name: Mapped[str] = mapped_column(index=True)
    year: Mapped[str] = mapped_column()
    genres: Mapped[str] = mapped_column()
    spotify_id: Mapped[str] = mapped_column(index=True)
    discogs_url: Mapped[str] = mapped_column(nullable=True)
    cover_image_url: Mapped[str] = mapped_column(nullable=True)
