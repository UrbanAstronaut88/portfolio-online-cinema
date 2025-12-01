from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, insert
from sqlalchemy.orm import joinedload, selectinload

from app.models.movies import (
    Movie as MovieModel,
    Genre,
    Star,
    Director,
    Certification,
    movie_genres,
    movie_directors,
    movie_stars,
)
from app.models.orders import OrderItem
from app.schemas.movies import MovieCreate


# -----------------------------
# CREATE MOVIE
# -----------------------------
async def create_movie(db: AsyncSession, movie: MovieCreate):

    # -------- CREATE MOVIE ITSELF ----------
    db_movie = MovieModel(
        name=movie.name,
        year=movie.year,
        time=movie.time,
        imdb=movie.imdb,
        votes=movie.votes,
        meta_score=movie.meta_score,
        gross=movie.gross,
        description=movie.description,
        price=movie.price,
        certification_id=movie.certification_id,
    )

    db.add(db_movie)
    await db.commit()
    await db.refresh(db_movie)

    movie_id = db_movie.id

    # -------- MANY-TO-MANY: GENRES ----------
    if movie.genres:
        # Validate IDs exist
        valid_genres = (await db.execute(
            select(Genre.id).where(Genre.id.in_(movie.genres))
        )).scalars().all()

        if valid_genres:
            await db.execute(
                insert(movie_genres),
                [{"movie_id": movie_id, "genre_id": g} for g in valid_genres]
            )

    # -------- MANY-TO-MANY: DIRECTORS ----------
    if movie.directors:
        valid_directors = (await db.execute(
            select(Director.id).where(Director.id.in_(movie.directors))
        )).scalars().all()

        if valid_directors:
            await db.execute(
                insert(movie_directors),
                [{"movie_id": movie_id, "director_id": d} for d in valid_directors]
            )

    # -------- MANY-TO-MANY: STARS ----------
    if movie.stars:
        valid_stars = (await db.execute(
            select(Star.id).where(Star.id.in_(movie.stars))
        )).scalars().all()

        if valid_stars:
            await db.execute(
                insert(movie_stars),
                [{"movie_id": movie_id, "star_id": s} for s in valid_stars]
            )

    # -------- FINAL COMMIT ----------
    await db.commit()

    # Reload movie with relationships for Swagger response
    result = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            selectinload(MovieModel.genres),
            selectinload(MovieModel.directors),
            selectinload(MovieModel.stars),
            selectinload(MovieModel.certification)
        )
    )
    return result.scalars().first()


# -----------------------------
# GET MOVIES LIST
# -----------------------------
async def get_movies(db: AsyncSession, skip: int = 0, limit: int = 20,
                     search: str = None, year: int = None,
                     sort_by: str = "name", order: str = "asc"):
    query = select(MovieModel).options(
        joinedload(MovieModel.genres),
        joinedload(MovieModel.directors),
        joinedload(MovieModel.stars),
        joinedload(MovieModel.certification)
    )

    if search:
        query = query.where(MovieModel.name.ilike(f"%{search}%") |
                            MovieModel.description.ilike(f"%{search}%"))

    if year:
        query = query.where(MovieModel.year == year)

    # sorting
    sort_field = getattr(MovieModel, sort_by, MovieModel.name)
    query = query.order_by(sort_field.desc() if order == "desc" else sort_field)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


# -----------------------------
# GET ONE MOVIE
# -----------------------------
async def get_movie_by_id(db: AsyncSession, movie_id: int):
    query = select(MovieModel).options(
        joinedload(MovieModel.genres),
        joinedload(MovieModel.directors),
        joinedload(MovieModel.stars),
        joinedload(MovieModel.certification),
    ).where(MovieModel.id == movie_id)

    result = await db.execute(query)
    return result.scalars().first()


# -----------------------------
# UPDATE MOVIE
# -----------------------------
async def update_movie(db: AsyncSession, movie_id: int, movie_update: MovieCreate):
    movie = await get_movie_by_id(db, movie_id)
    if not movie:
        return None

    # simple field update
    movie.name = movie_update.name
    movie.year = movie_update.year
    movie.time = movie_update.time
    movie.imdb = movie_update.imdb
    movie.votes = movie_update.votes
    movie.meta_score = movie_update.meta_score
    movie.gross = movie_update.gross
    movie.description = movie_update.description
    movie.price = movie_update.price
    movie.certification_id = movie_update.certification_id

    # relationships: recreating
    movie.genres = []
    if movie_update.genres:
        genres = (await db.execute(select(Genre).where(Genre.id.in_(movie_update.genres)))).scalars().all()
        movie.genres = genres

    movie.directors = []
    if movie_update.directors:
        directors = (await db.execute(select(Director).where(Director.id.in_(movie_update.directors)))).scalars().all()
        movie.directors = directors

    movie.stars = []
    if movie_update.stars:
        stars = (await db.execute(select(Star).where(Star.id.in_(movie_update.stars)))).scalars().all()
        movie.stars = stars

    await db.commit()
    await db.refresh(movie)
    return movie


# -----------------------------
# DELETE MOVIE
# -----------------------------
async def delete_movie(db: AsyncSession, movie_id: int):
    # You cannot delete a purchased film
    purchased_result = await db.execute(
        select(func.count(OrderItem.id)).where(OrderItem.movie_id == movie_id)
    )
    purchased_count = purchased_result.scalar()

    if purchased_count > 0:
        raise ValueError("Cannot delete movie that has been purchased")

    # удаляем связи
    await db.execute(delete(movie_genres).where(movie_genres.c.movie_id == movie_id))
    await db.execute(delete(movie_directors).where(movie_directors.c.movie_id == movie_id))
    await db.execute(delete(movie_stars).where(movie_stars.c.movie_id == movie_id))

    movie = await get_movie_by_id(db, movie_id)
    if movie:
        await db.delete(movie)
        await db.commit()
        return True

    return False


# -----------------------------
# GENRES STATISTICS
# -----------------------------
async def get_genres_with_count(db: AsyncSession):
    query = (
        select(Genre, func.count(movie_genres.c.movie_id).label("movie_count"))
        .outerjoin(movie_genres)
        .group_by(Genre.id)
    )

    result = await db.execute(query)
    return result.all()
