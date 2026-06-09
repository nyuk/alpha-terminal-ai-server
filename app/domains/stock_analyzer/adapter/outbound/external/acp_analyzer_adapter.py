import json
from datetime import datetime
from typing import Any

import httpx

from app.domains.stock_analyzer.adapter.outbound.external.openai_analyzer_adapter import (
    MULTI_ARTICLE_PROMPT_TEMPLATE,
    PROMPT_TEMPLATE,
    _build_analyzed_article,
)
from app.domains.stock_analyzer.application.usecase.article_analyzer_port import ArticleAnalyzerPort
from app.domains.stock_analyzer.domain.entity.analyzed_article import AnalyzedArticle

FALLBACK_NOTICE_PREFIX = "[ACP 모델 출력 품질 기준 미달 - OpenAI fallback 사용]"
FALLBACK_NOTICE_HELP = (
    "이 표시는 기사 원문 길이가 부족하다는 뜻이 아니라, ACP/Ollama 모델이 만든 분석 JSON의 "
    "summary가 비었거나 형식 기준을 통과하지 못했다는 뜻입니다. Ollama 로컬 모델의 JSON 분석 "
    "안정성 문제일 수 있습니다."
)


class ACPAnalyzerAdapter(ArticleAnalyzerPort):
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        fallback_adapter: ArticleAnalyzerPort | None = None,
        timeout_seconds: float = 8.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key.strip()
        self._model = model
        self._fallback_adapter = fallback_adapter
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    async def analyze(
        self,
        article_id: str,
        title: str,
        body: str,
        category: str,
    ) -> AnalyzedArticle:
        prompt = PROMPT_TEMPLATE.format(
            category=category,
            title=title,
            body=body[:3000],
        )

        try:
            data = await self._request_json_object(
                prompt=prompt,
                metadata={
                    "project": "alpha-desk",
                    "task": "stock-summary",
                    "article_id": article_id,
                    "category": category,
                },
            )
            return _build_analyzed_article(
                article_id=article_id,
                data=data,
                default_confidence=0.5,
            )
        except Exception as exc:
            if self._fallback_adapter is None:
                raise
            fallback = await self._fallback_adapter.analyze(article_id, title, body, category)
            return _with_fallback_notice(fallback, exc)

    async def synthesize_articles(
        self,
        symbol: str,
        name: str,
        articles: list[dict],
    ) -> AnalyzedArticle:
        articles_text_parts = []
        for i, art in enumerate(articles, 1):
            part = (
                f"[기사 {i}] {art.get('published_at', '날짜 미상')}\n"
                f"제목: {art.get('title', '')}\n"
                f"내용: {art.get('body', '')[:800]}"
            )
            articles_text_parts.append(part)
        articles_text = "\n\n".join(articles_text_parts)

        prompt = MULTI_ARTICLE_PROMPT_TEMPLATE.format(
            symbol=symbol,
            name=name,
            count=len(articles),
            articles_text=articles_text,
        )

        try:
            data = await self._request_json_object(
                prompt=prompt,
                metadata={
                    "project": "alpha-desk",
                    "task": "stock-summary",
                    "symbol": symbol,
                    "name": name,
                    "article_count": str(len(articles)),
                },
            )
            synthesis_id = f"synthesis_{symbol}_{int(datetime.now().timestamp())}"
            return _build_analyzed_article(
                article_id=synthesis_id,
                data=data,
                default_confidence=0.85,
            )
        except Exception as exc:
            if self._fallback_adapter is None:
                raise
            fallback = await self._fallback_adapter.synthesize_articles(symbol, name, articles)
            return _with_fallback_notice(fallback, exc)

    async def _request_json_object(
        self,
        prompt: str,
        metadata: dict[str, str],
    ) -> dict[str, Any]:
        headers = {"content-type": "application/json"}
        if self._api_key:
            headers["authorization"] = f"Bearer {self._api_key}"

        async with httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout_seconds,
            transport=self._transport,
        ) as client:
            response = await client.post(
                "/v1/chat/completions",
                headers=headers,
                json={
                    "model": self._model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_tokens": 800,
                    "stream": False,
                    "response_format": {"type": "json_object"},
                    "metadata": metadata,
                },
            )

        if response.status_code >= 400:
            try:
                error_payload = response.json()
            except json.JSONDecodeError:
                error_payload = {"error": response.text}
            raise RuntimeError(
                "ACP gateway returned HTTP "
                f"{response.status_code}: {_format_gateway_error(error_payload)}"
            )

        payload = response.json()
        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("ACP gateway response is missing choices[0].message.content.") from exc

        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"ACP gateway returned invalid JSON content: {_truncate(str(content), 700)}") from exc
        if not isinstance(data, dict):
            raise RuntimeError(
                "ACP gateway response_format=json_object returned non-object JSON: "
                f"{_truncate(str(content), 700)}"
            )

        return data


def _with_fallback_notice(analysis: AnalyzedArticle, error: Exception) -> AnalyzedArticle:
    return AnalyzedArticle(
        article_id=analysis.article_id,
        summary=(
            f"{FALLBACK_NOTICE_PREFIX}\n"
            f"설명: {FALLBACK_NOTICE_HELP}\n"
            f"미달 내용: {_truncate(str(error), 700)}\n\n"
            f"[OpenAI 분석]\n{analysis.summary}"
        ),
        tags=analysis.tags,
        sentiment=analysis.sentiment,
        sentiment_score=analysis.sentiment_score,
        confidence=analysis.confidence,
        analyzer_version=f"{analysis.analyzer_version}+acp-fallback",
    )


def _format_gateway_error(payload: Any) -> str:
    if not isinstance(payload, dict):
        return _truncate(str(payload), 1000)

    error = str(payload.get("error", "")).strip()
    rejected_content = str(payload.get("rejectedContent", "")).strip()
    parts = []
    if error:
        parts.append(f"reason={error}")
    if rejected_content:
        parts.append(f"rejectedContent={rejected_content}")
    return _truncate("; ".join(parts) or str(payload), 1000)


def _truncate(value: str, max_length: int) -> str:
    return value if len(value) <= max_length else f"{value[:max_length]}..."
