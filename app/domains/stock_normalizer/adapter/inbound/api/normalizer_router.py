from fastapi import APIRouter, HTTPException

from app.domains.stock_normalizer.adapter.outbound.persistence.normalized_disclosure_repository_impl import InMemoryNormalizedDisclosureRepository
from app.domains.stock_normalizer.infrastructure.repository_registry import normalized_article_repository
from app.domains.stock_normalizer.application.request.normalize_disclosure_request import NormalizeDisclosureRequest
from app.domains.stock_normalizer.application.request.normalize_raw_article_request import NormalizeRawArticleRequest
from app.domains.stock_normalizer.application.response.normalize_disclosure_response import NormalizeDisclosureResponse
from app.domains.stock_normalizer.application.response.normalize_raw_article_response import NormalizeRawArticleResponse
from app.domains.stock_normalizer.application.usecase.normalize_disclosure_usecase import NormalizeDisclosureUseCase
from app.domains.stock_normalizer.application.usecase.normalize_raw_article_usecase import NormalizeRawArticleUseCase

router = APIRouter(prefix="/normalizer", tags=["stock_normalizer"])

_disclosure_repository = InMemoryNormalizedDisclosureRepository()
_article_repository = normalized_article_repository


@router.post("/disclosures", response_model=NormalizeDisclosureResponse, status_code=201)
async def normalize_disclosure(request: NormalizeDisclosureRequest):
    try:
        return await NormalizeDisclosureUseCase(_disclosure_repository).execute(request)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/articles", response_model=NormalizeRawArticleResponse, status_code=201)
async def normalize_raw_article(request: NormalizeRawArticleRequest):
    try:
        return await NormalizeRawArticleUseCase(_article_repository).execute(request)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
