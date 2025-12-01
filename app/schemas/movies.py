from pydantic import BaseModel
from typing import List, Optional


# ========== GENRE ==========
class GenreBase(BaseModel):
    name: str


class Genre(GenreBase):
    id: int

    class Config:
        from_attributes = True


# ========== STAR ==========
class StarBase(BaseModel):
    name: str


class Star(StarBase):
    id: int

    class Config:
        from_attributes = True


# ========== DIRECTOR ==========
class DirectorBase(BaseModel):
    name: str


class Director(DirectorBase):
    id: int

    class Config:
        from_attributes = True


# ========== CERTIFICATION ==========
class CertificationBase(BaseModel):
    name: str


class Certification(CertificationBase):
    id: int

    class Config:
        from_attributes = True


# ========== MOVIE CREATE (INPUT) ==========
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

    # Input: IDs ONLY
    genres: List[int] = []
    directors: List[int] = []
    stars: List[int] = []


class MovieCreate(MovieBase):
    pass


# ========== MOVIE RESPONSE (OUTPUT) ==========
class Movie(BaseModel):
    id: int
    uuid: str
    name: str
    year: int
    time: int
    imdb: float
    votes: int
    meta_score: Optional[float]
    gross: Optional[float]
    description: str
    price: float

    # Output: nested objects
    certification: Certification
    genres: List[Genre]
    directors: List[Director]
    stars: List[Star]

    class Config:
        from_attributes = True
