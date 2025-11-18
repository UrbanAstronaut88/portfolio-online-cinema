from sqlalchemy import Column, String, Float, Text, ForeignKey, Table, UniqueConstraint, Integer
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid


# Associative tables (many-to-many)
movie_genres = Table(
    "movie_genres",
    Base.metadata,
    Column("movie_id", Integer, ForeignKey("movies.id"), primary_key=True),
    Column("genre_id", Integer, ForeignKey("genres.id"), primary_key=True)
)

movie_directors = Table(
    "movie_directors",
    Base.metadata,
    Column("movie_id", Integer, ForeignKey("movies.id"), primary_key=True),
    Column("director_id", Integer, ForeignKey("directors.id"), primary_key=True)
)

movie_stars = Table(
    "movie_stars",
    Base.metadata,
    Column("movie_id", Integer, ForeignKey("movies.id"), primary_key=True),
    Column("star_id", Integer, ForeignKey("stars.id"), primary_key=True)
)


class Genre(Base):
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    movies = relationship("Movie", secondary=movie_genres, back_populates="genres")


class Star(Base):
    __tablename__ = "stars"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    movies = relationship("Movie", secondary=movie_stars, back_populates="stars")


class Director(Base):
    __tablename__ = "directors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    movies = relationship("Movie", secondary=movie_directors, back_populates="directors")


class Certification(Base):
    __tablename__ = "certifications"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    movies = relationship("Movie", back_populates="certification")


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    time = Column(Integer, nullable=False)
    imdb = Column(Float, nullable=False)
    votes = Column(Integer, nullable=False)
    meta_score = Column(Float, nullable=True)
    gross = Column(Float, nullable=True)
    description = Column(Text, nullable=False)
    price = Column(Float, nullable=False)  # DECIMAL(10,2) в SQL, но Float для простоты <<<<<< позже изменить
    certification_id = Column(Integer, ForeignKey("certifications.id"), nullable=False)

    certification = relationship("Certification", back_populates="movies")
    genres = relationship("Genre", secondary=movie_genres, back_populates="movies")
    directors = relationship("Director", secondary=movie_directors,back_populates="movies")
    stars = relationship("Star", secondary=movie_stars, back_populates="movies")

    __table_args__ = (UniqueConstraint("name", "year", "time", name="unique_movie"),)
