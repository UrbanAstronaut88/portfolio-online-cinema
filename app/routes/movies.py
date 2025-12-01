from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.schemas.movies import Movie, MovieCreate
from app.crud.movies import (
    create_movie,
    get_movies,
    get_movie_by_id,
    update_movie,
    delete_movie,
    get_genres_with_count
)
from app.utils.auth import get_current_user
from app.models.accounts import User


router = APIRouter(prefix="/movies", tags=["movies"])


# ---------------------------
# CREATE MOVIE
# ---------------------------
@router.post("/", response_model=Movie)
async def create(
    movie: MovieCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Roles check
    if current_user.group is None or current_user.group.name not in ["MODERATOR", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    created_movie = await create_movie(db, movie)
    return created_movie


# ---------------------------
# LIST MOVIES (filters, sorting)
# ---------------------------
@router.get("/", response_model=List[Movie])
async def read_movies(
    skip: int = 0,
    limit: int = Query(10, le=100),
    search: str | None = None,
    year: int | None = None,
    sort_by: str = Query("name", description="Sort by field: name, price, year, etc."),
    order: str = Query("asc", description="Order: asc or desc"),
    db: AsyncSession = Depends(get_db)
):
    movies = await get_movies(
        db,
        skip=skip,
        limit=limit,
        search=search,
        year=year,
        sort_by=sort_by,
        order=order
    )
    return movies


# ---------------------------
# GET MOVIE BY ID
# ---------------------------
@router.get("/{movie_id}", response_model=Movie)
async def read_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await get_movie_by_id(db, movie_id)
    if not movie:
        raise HTTPException(404, "Movie not found")
    return movie


# ---------------------------
# UPDATE MOVIE
# ---------------------------
@router.put("/{movie_id}", response_model=Movie)
async def update(
    movie_id: int,
    movie_update: MovieCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.group is None or current_user.group.name not in ["MODERATOR", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    updated_movie = await update_movie(db, movie_id, movie_update)
    if not updated_movie:
        raise HTTPException(404, "Movie not found")

    return updated_movie


# ---------------------------
# DELETE MOVIE
# ---------------------------
@router.delete("/{movie_id}")
async def delete(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.group is None or current_user.group.name not in ["MODERATOR", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        success = await delete_movie(db, movie_id)
        if not success:
            raise HTTPException(404, "Movie not found")
        return {"message": "Movie deleted"}
    except ValueError as e:
        raise HTTPException(400, str(e))


# ---------------------------
# GENRES WITH MOVIE COUNT
# ---------------------------
@router.get("/genres", response_model=List[dict])
async def get_genres(db: AsyncSession = Depends(get_db)):
    data = await get_genres_with_count(db)
    return [
        {"id": genre.id, "name": genre.name, "movie_count": count}
        for genre, count in data
    ]
