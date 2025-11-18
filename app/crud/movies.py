from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from app.models.movies import Movie, Genre, Star, Director, Certification
from app.schemas.movies import MovieCreate


def create_movie(db: Session, movie: MovieCreate):
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
    db.commit()
    db.refresh(db_movie)

    # Добавляем связи
    for genre_id in movie.genres:
        genre = db.query(Genre).filter(Genre.id == genre_id).first()
        if genre:
            db_movie.genres.append(genre)

    db.commit()
    return db_movie


def get_movies(db: Session, skip: int = 0, limit: int = 20, search: str = None, year: int = None):
    query = db.query(Movie).options(joinedload(Movie.genres), joinedload(Movie.directors), joinedload(Movie.stars), joinedload(Movie.certification))
    if search:
        query = query.filter(or_(Movie.name.ilike(f"%{search}%"), Movie.description.ilike(f"%{search}%")))
    if year:
        query = query.filter(Movie.year == year)
    return query.offset(skip).limit(limit).all()


# позже добавить delete_movie, update_movie, etc
# для модераторов: prevent delete if purchased (нужно связать с orders позже) !!! <<<
