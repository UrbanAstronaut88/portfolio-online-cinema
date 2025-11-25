# app/routes/movies.py (обновлённый для production: async, auth с ролями, добавлены роутеры, filters/sort)
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_db
from app.schemas.movies import Movie, MovieCreate
from app.crud.movies import create_movie, get_movies, get_movie_by_id, update_movie, delete_movie, get_genres_with_count
from app.utils.auth import get_current_user
from app.models.accounts import User

router = APIRouter(prefix="/movies", tags=["movies"])


@router.post("/", response_model=Movie)
async def create(movie: MovieCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.group.name not in ["MODERATOR", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return await create_movie(db, movie)


@router.get("/", response_model=List[Movie])
async def read_movies(
    skip: int = 0,
    limit: int = Query(10, le=100),
    search: str = None,
    year: int = None,
    sort_by: str = Query("name", description="Sort by field: name, price, year, etc."),
    order: str = Query("asc", description="Order: asc or desc"),
    db: AsyncSession = Depends(get_db)
):
    return await get_movies(db, skip=skip, limit=limit, search=search, year=year, sort_by=sort_by, order=order)


@router.get("/{movie_id}", response_model=Movie)
async def read_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await get_movie_by_id(db, movie_id)
    if not movie:
        raise HTTPException(404, "Movie not found")
    return movie


@router.put("/{movie_id}", response_model=Movie)
async def update(movie_id: int, movie_update: MovieCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.group.name not in ["MODERATOR", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    updated = await update_movie(db, movie_id, movie_update)
    if not updated:
        raise HTTPException(404, "Movie not found")
    return updated


@router.delete("/{movie_id}")
async def delete(movie_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.group.name not in ["MODERATOR", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    try:
        success = await delete_movie(db, movie_id)
        if not success:
            raise HTTPException(404, "Movie not found")
        return {"message": "Movie deleted"}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/genres", response_model=List[dict])  # We are returning list of {"id": int, "name": str, "movie_count": int}
async def get_genres(db: AsyncSession = Depends(get_db)):
    genres_with_count = await get_genres_with_count(db)
    return [{"id": genre.id, "name": genre.name, "movie_count": count} for genre, count in genres_with_count]
