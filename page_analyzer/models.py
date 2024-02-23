import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, func, ForeignKey


class Base(DeclarativeBase):
    pass


class UrlsModel(Base):
    __tablename__ = "urls"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(), server_default=func.now())


class UrlChecksModel(Base):
    __tablename__ = "url_checks"

    id: Mapped[int] = mapped_column(primary_key=True)
    url_id: Mapped[int] = mapped_column(ForeignKey('urls.id'))
    status_code: Mapped[int]
    h1: Mapped[str]
    title: Mapped[str]
    description: Mapped[str]
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(), server_default=func.now())
