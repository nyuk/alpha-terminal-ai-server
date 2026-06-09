import httpx

from app.domains.market_analysis.adapter.outbound.external.langchain_qa_adapter import (
    _OUT_OF_SCOPE_MARKER,
    _PERSONALIZATION_MARKER,
    _SYSTEM_PROMPT,
)
from app.domains.market_analysis.application.usecase.langchain_qa_port import LangChainQAPort
from app.domains.market_analysis.domain.entity.analysis_answer import AnalysisAnswer


class ACPMarketAnalysisQAAdapter(LangChainQAPort):
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        fallback_adapter: LangChainQAPort | None = None,
        timeout_seconds: float = 20.0,
        transport: httpx.BaseTransport | None = None,
    ):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key.strip()
        self._model = model
        self._fallback_adapter = fallback_adapter
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    def ask(self, question: str, context: str) -> AnalysisAnswer:
        try:
            answer = self._request_answer(question=question, context=context)
            return AnalysisAnswer(
                answer=answer,
                in_scope=_OUT_OF_SCOPE_MARKER not in answer,
                is_personalized=_PERSONALIZATION_MARKER in context,
            )
        except Exception as exc:
            if self._fallback_adapter is None:
                return AnalysisAnswer(answer=f"분석 중 오류가 발생했습니다: {exc}", in_scope=False)
            return self._fallback_adapter.ask(question, context)

    def _request_answer(self, question: str, context: str) -> str:
        headers = {"content-type": "application/json"}
        if self._api_key:
            headers["authorization"] = f"Bearer {self._api_key}"

        system_prompt = _SYSTEM_PROMPT.replace("{out_of_scope_marker}", _OUT_OF_SCOPE_MARKER)

        with httpx.Client(
            base_url=self._base_url,
            timeout=self._timeout_seconds,
            transport=self._transport,
        ) as client:
            response = client.post(
                "/v1/chat/completions",
                headers=headers,
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": system_prompt.format(context=context)},
                        {"role": "user", "content": question},
                    ],
                    "temperature": 0.2,
                    "max_tokens": 1400,
                    "stream": False,
                    "metadata": {
                        "project": "alpha-desk",
                        "task": "ai-briefing",
                        "surface": "market-analysis.ask",
                    },
                },
            )

        if response.status_code >= 400:
            raise RuntimeError(f"ACP gateway returned HTTP {response.status_code}: {response.text}")

        payload = response.json()
        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("ACP gateway response is missing choices[0].message.content.") from exc

        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("ACP gateway returned an empty answer.")
        return content
