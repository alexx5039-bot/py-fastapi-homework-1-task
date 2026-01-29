from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_db
from database.models import MovieModel
from schemas import MovieDetailResponseSchema
from schemas.movies import MovieListResponseSchema

router = APIRouter(prefix="/movies", tags=["movies"])

BASE_URL = "/theater/movies/"


@router.get("/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * per_page

    total_items = await db.scalar(
        select(func.count()).select_from(MovieModel)
    )

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page

    result = await db.execute(
        select(MovieModel)
        .offset(offset)
        .limit(per_page)
    )
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    prev_page = (
        f"{BASE_URL}?page={page - 1}&per_page={per_page}"
        if page > 1
        else None
    )
    next_page = (
        f"{BASE_URL}?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
    )

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.get("/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_movie_by_id(
        movie_id: int,
        db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )
    return movie
