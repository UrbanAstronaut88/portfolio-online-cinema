from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.schemas.movies import Movie, MovieCreate
from app.crud.movies import create_movie, get_movies
# добавь depends для current_user и checks для ролей (позже, с auth)


router = APIRouter(prefix="/movies", tags=["movies"])

@router.post("/", response_model=Movie)
def create(movie: MovieCreate, db: Session = Depends(get_db)):
    # только для модераторов/admin (добавь security позже)
    return create_movie(db, movie)

@router.get("/", response_model=List[Movie])
def read_movies(skip: int = 0, limit: int = Query(10, le=100), search: str = None, year: int = None, db: Session = Depends(get_db)):
    return get_movies(db, skip=skip, limit=limit, search=search, year=year)

# Добавь /genres, /{id}, update, delete, filters/sort, favorites, ratings, comments
# Для жанров: get genres with movie count