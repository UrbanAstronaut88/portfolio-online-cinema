from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, func, delete
from app.models.movies import Movie, Genre, Star, Director, Certification, movie_genres, movie_directors, movie_stars
from app.schemas.movies import MovieCreate, Movie
from app.models.orders import OrderItem


async def create_movie(db: AsyncSession, movie: MovieCreate):
    db_movie = Movie(
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

    # adding relationships (many-to-many)
    for genre_id in movie.genres:
        genre_result = await db.execute(select(Genre).where(Genre.id == genre_id))
        genre = genre_result.scalars().first()
        if genre:
            db_movie.genres.append(genre)
    for director_id in movie.directors:
        director_result = await db.execute(select(Director).where(Director.id == director_id))
        director = director_result.scalars().first()
        if director:
            db_movie.directors.append(director)
    for star_id in movie.stars:
        star_result = await db.execute(select(Star).where(Star.id == star_id))
        star = star_result.scalars().first()
        if star:
            db_movie.stars.append(star)

    await db.commit()
    return db_movie


async def get_movies(db: AsyncSession, skip: int = 0, limit: int = 20, search: str = None, year: int = None,
                     sort_by: str = "name", order: str = "asc"):
    query = select(Movie).options(
        joinedload(Movie.genres),
        joinedload(Movie.directors),
        joinedload(Movie.stars),
        joinedload(Movie.certification)
    )
    if search:
        query = query.where(or_(Movie.name.ilike(f"%{search}%"), Movie.description.ilike(f"%{search}%")))
    if year:
        query = query.where(Movie.year == year)

    # Сортировка
    sort_field = getattr(Movie, sort_by, Movie.name)
    if order.lower() == "desc":
        query = query.order_by(sort_field.desc())
    else:
        query = query.order_by(sort_field)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def get_movie_by_id(db: AsyncSession, movie_id: int):
    query = select(Movie).options(
        joinedload(Movie.genres),
        joinedload(Movie.directors),
        joinedload(Movie.stars),
        joinedload(Movie.certification)
    ).where(Movie.id == movie_id)
    result = await db.execute(query)
    return result.scalars().first()


async def update_movie(db: AsyncSession, movie_id: int, movie_update: MovieCreate):
    movie = await get_movie_by_id(db, movie_id)
    if not movie:
        return None

    # Updating fields
    movie.name = movie_update.name or movie.name
    movie.year = movie_update.year or movie.year
    movie.time = movie_update.time or movie.time
    movie.imdb = movie_update.imdb or movie.imdb
    movie.votes = movie_update.votes or movie.votes
    movie.meta_score = movie_update.meta_score or movie.meta_score
    movie.gross = movie_update.gross or movie.gross
    movie.description = movie_update.description or movie.description
    movie.price = movie_update.price or movie.price
    movie.certification_id = movie_update.certification_id or movie.certification_id

    # Updating relationships (cleaning up and adding new ones)
    movie.genres = []
    for genre_id in movie_update.genres:
        genre_result = await db.execute(select(Genre).where(Genre.id == genre_id))
        genre = genre_result.scalars().first()
        if genre:
            movie.genres.append(genre)
    movie.directors = []
    for director_id in movie_update.directors:
        director_result = await db.execute(select(Director).where(Director.id == director_id))
        director = director_result.scalars().first()
        if director:
            movie.directors.append(director)
    movie.stars = []
    for star_id in movie_update.stars:
        star_result = await db.execute(select(Star).where(Star.id == star_id))
        star = star_result.scalars().first()
        if star:
            movie.stars.append(star)

    await db.commit()
    await db.refresh(movie)
    return movie


async def delete_movie(db: AsyncSession, movie_id: int):
    # Checking whether the film has been purchased (whether there is an OrderItem)
    purchased_result = await db.execute(select(func.count(OrderItem.id)).where(OrderItem.movie_id == movie_id))
    purchased_count = purchased_result.scalar()
    if purchased_count > 0:
        raise ValueError("Cannot delete movie that has been purchased")

    # Deleting relationships
    await db.execute(delete(movie_genres).where(movie_genres.c.movie_id == movie_id))
    await db.execute(delete(movie_directors).where(movie_directors.c.movie_id == movie_id))
    await db.execute(delete(movie_stars).where(movie_stars.c.movie_id == movie_id))

    # Deleting movie
    movie = await get_movie_by_id(db, movie_id)
    if movie:
        await db.delete(movie)
        await db.commit()
        return True
    return False


async def get_genres_with_count(db: AsyncSession):
    query = select(Genre, func.count(movie_genres.c.movie_id).label("movie_count")).outerjoin(movie_genres).group_by(
        Genre.id)
    result = await db.execute(query)
    return result.all()
