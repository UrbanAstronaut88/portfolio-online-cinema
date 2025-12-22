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
    get_genres_with_count,
)
from app.utils.auth import get_current_user
from app.models.accounts import User

router = APIRouter(prefix="/movies", tags=["movies"])


@router.get(
    "/genres",
    response_model=List[dict],
    summary="List genres with movie count",
    description="Returns all genres with number of movies in each genre.",
)
async def get_genres(db: AsyncSession = Depends(get_db)):
    data = await get_genres_with_count(db)
    return [{"id": g.id, "name": g.name, "movie_count": count} for g, count in data]


@router.post(
    "/",
    response_model=Movie,
    summary="Create movie",
    description="ADMIN and MODERATOR only. Creates a new movie.",
)
async def create(
    movie: MovieCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.group is None or current_user.group.name not in ["MODERATOR", "ADMIN"]:
        raise HTTPException(403, "Not authorized")

    return await create_movie(db, movie)


@router.get(
    "/",
    response_model=List[Movie],
    summary="List movies",
    description="Returns movies with filtering, search, sorting and pagination.",
)
async def read_movies(
    skip: int = 0,
    limit: int = Query(10, le=100),
    search: str | None = None,
    year: int | None = None,
    sort_by: str = Query("name"),
    order: str = Query("asc"),
    db: AsyncSession = Depends(get_db),
):
    return await get_movies(
        db,
        skip=skip,
        limit=limit,
        search=search,
        year=year,
        sort_by=sort_by,
        order=order,
    )


@router.get(
    "/{movie_id}",
    response_model=Movie,
    summary="Get movie by ID",
    description="Returns a single movie by its ID.",
)
async def read_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await get_movie_by_id(db, movie_id)
    if not movie:
        raise HTTPException(404, "Movie not found")
    return movie


@router.put(
    "/{movie_id}",
    response_model=Movie,
    summary="Update movie",
    description="ADMIN and MODERATOR only. Updates movie data.",
)
async def update(
    movie_id: int,
    movie_update: MovieCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.group is None or current_user.group.name not in ["MODERATOR", "ADMIN"]:
        raise HTTPException(403, "Not authorized")

    updated = await update_movie(db, movie_id, movie_update)
    if not updated:
        raise HTTPException(404, "Movie not found")
    return updated


@router.delete(
    "/{movie_id}",
    summary="Delete movie",
    description="ADMIN and MODERATOR only. Deletes a movie.",
)
async def delete(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.group is None or current_user.group.name not in ["MODERATOR", "ADMIN"]:
        raise HTTPException(403, "Not authorized")

    success = await delete_movie(db, movie_id)
    if not success:
        raise HTTPException(404, "Movie not found")

    return {"message": "Movie deleted"}
