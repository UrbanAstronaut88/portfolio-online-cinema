from pydantic import BaseModel
from typing import List, Optional


class GenreBase(BaseModel):
    name: str


class Genre(GenreBase):
    id: int

    class Config:
        from_attributes = True


class StarBase(BaseModel):
    name: str


class Star(StarBase):
    id: int

    class Config:
        from_attributes = True


class DirectorBase(BaseModel):
    name: str


class Director(DirectorBase):
    id: int

    class Config:
        from_attributes = True


class CertificationBase(BaseModel):
    name: str


class Certification(CertificationBase):
    id: int

    class Config:
        from_attributes = True


class MovieBase(BaseModel):
    name: str
    year: int
    time: int
    imdb: float
    votes: int
    meta_score: Optional[float] = None
    gross: Optional[float] = None
    description: str
    price: float
    certification_id: int
    genres: List[int] = []  # IDs genres
    directors: List[int] = []  # IDs directors
    stars: List[int] = []  # IDs stars


class MovieCreate(MovieBase):
    pass


class Movie(MovieBase):
    id: int
    uuid: str

    class Config:
        from_attributes = True


