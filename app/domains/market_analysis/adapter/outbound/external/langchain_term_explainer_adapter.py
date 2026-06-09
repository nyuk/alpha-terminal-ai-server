from typing import Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.domains.market_analysis.application.usecase.term_explainer_port import TermExplainerPort
from app.domains.market_analysis.domain.entity.analysis_answer import AnalysisAnswer

_SYSTEM_PROMPT = """당신은 AI_BRIEFING 안에서 주식/금융 용어를 설명하는 보조자입니다.

규칙:
- 매수, 매도, 보유, 관망 같은 투자 판단 용어도 설명할 수 있습니다.
- 용어 설명은 쉽고 짧게 작성합니다.
- 특정 종목 맥락이 있으면 그 맥락에 맞춰 설명합니다.
- 답변은 3문장 이내로 작성합니다.
- 반드시 아래 형식으로 답합니다.

[설명 내용]
예시: [실생활 예시 한 문장]
"""

_HUMAN_PROMPT = """{context_line}용어: {term}"""


class LangChainTermExplainerAdapter(TermExplainerPort):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        llm = ChatOpenAI(api_key=api_key, model=model)
        prompt = ChatPromptTemplate.from_messages([
            ("system", _SYSTEM_PROMPT),
            ("human", _HUMAN_PROMPT),
        ])
        self._chain = prompt | llm | StrOutputParser()

    def explain(self, term: str, context: Optional[str] = None) -> AnalysisAnswer:
        context_line = f"맥락: {context}\n" if context else ""
        try:
            answer = self._chain.invoke({"term": term, "context_line": context_line})
            return AnalysisAnswer(answer=answer, in_scope=True)
        except Exception as e:
            return AnalysisAnswer(answer=f"설명 중 오류가 발생했습니다: {e}", in_scope=False)
