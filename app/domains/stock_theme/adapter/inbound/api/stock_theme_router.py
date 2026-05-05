from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.domains.stock_theme.adapter.outbound.persistence.stock_theme_repository_impl import (
    StockThemeRepositoryImpl,
)
from app.domains.stock_theme.application.response.stock_theme_response import (
    StockThemeListResponse,
)
from app.domains.stock_theme.application.usecase.get_stock_themes_usecase import GetStockThemesUseCase
from app.domains.stock_theme.application.usecase.seed_stock_themes_usecase import SeedStockThemesUseCase
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/stock-theme", tags=["stock-theme"])

_DISABLED_DETAIL = (
    "Stock recommendation endpoints are disabled for StockBrief. "
    "Use fact-based watchlist summaries, theme matches, and risk briefings instead."
)


@router.get("", response_model=StockThemeListResponse)
async def get_stock_themes(
    theme: Optional[str] = Query(default=None, description="Filter by theme keyword"),
    db: Session = Depends(get_db),
):
    repository = StockThemeRepositoryImpl(db)
    usecase = GetStockThemesUseCase(repository)
    return usecase.execute(theme=theme)


class RecommendRequest(BaseModel):
    keywords: dict[str, int]


@router.get("/recommend", response_model=dict)
async def recommend_stocks_from_keywords():
    raise HTTPException(status_code=410, detail=_DISABLED_DETAIL)


@router.post("/recommend", response_model=dict)
async def recommend_stocks(_request: RecommendRequest):
    raise HTTPException(status_code=410, detail=_DISABLED_DETAIL)


@router.post("/seed", response_model=dict)
async def seed_stock_themes(db: Session = Depends(get_db)):
    repository = StockThemeRepositoryImpl(db)
    usecase = SeedStockThemesUseCase(repository)
    count = usecase.execute()
    return {"message": f"{count} stock-theme mappings saved"}
