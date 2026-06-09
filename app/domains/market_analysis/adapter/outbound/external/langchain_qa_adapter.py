from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.domains.market_analysis.application.usecase.langchain_qa_port import LangChainQAPort
from app.domains.market_analysis.domain.entity.analysis_answer import AnalysisAnswer

_OUT_OF_SCOPE_MARKER = "관심종목 범위를 벗어납니다."

_PERSONALIZATION_MARKER = "[사용자 투자 성향]"

_SYSTEM_PROMPT = """당신은 개인용 AI_BRIEFING 투자 분석 보조자입니다.
아래 컨텍스트는 사용자의 관심종목, 테마, 투자 성향 정보입니다.

{context}

답변 원칙:
- 사용자가 묻는 뉴스, 공시, 리포트, 시장 맥락, 리스크, 매수/매도 추천, 보유/관망 판단을 하나의 AI_BRIEFING 답변으로 정리합니다.
- 사용자의 투자 성향 정보가 있다면 답변의 관점과 우선순위에 반영합니다.
- 매수, 매도, 보유, 관망, 비중 축소/확대 같은 투자 판단과 추천 표현을 사용할 수 있습니다.
- 사용자가 추천을 요구하면 결론을 피하지 말고, 근거와 리스크를 붙여 명확한 판단을 제시합니다.
- 수익률, 목표가, 확정적 미래는 근거가 없으면 만들지 않습니다.
- 제공된 컨텍스트에 없는 최신 실적, 주가 흐름, PER/PBR 같은 밸류에이션, 가격 지표, 시장 점유율은 단정하지 않습니다.
- 확인되지 않은 수치나 최신 데이터가 필요하면 "확인 필요" 또는 "다음에 확인할 데이터"로 분리합니다.
- 사용자가 손절률, 목표 수익률, 비중 같은 숫자를 주지 않았다면 구체적인 숫자를 만들지 말고 "보수적/중립/공격적 기준"처럼 범주형으로 제시합니다.
- 외부 실시간 시세나 리포트 원문을 직접 조회한 것처럼 말하지 않습니다.
- 질문이 관심종목이나 관련 테마와 무관하면 "{out_of_scope_marker}"라고 안내합니다.
- 답변은 한국어로 작성합니다.

권장 답변 구조:
1. 결론: 사용자가 바로 이해할 수 있게 한 줄로 정리
2. 판단 근거: 관심종목 테마/최근 요약에서 확인되는 핵심 근거
3. 리스크: 반대 시나리오와 손실 요인
4. 매수/매도/보유 추천: 현재 관점에서 무엇을 권하는지와 조건 정리
5. 확인할 데이터: 다음에 봐야 할 뉴스, 공시, 실적, 가격 수급 지표"""


class LangChainQAAdapter(LangChainQAPort):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        llm = ChatOpenAI(api_key=api_key, model=model)
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                _SYSTEM_PROMPT.replace("{out_of_scope_marker}", _OUT_OF_SCOPE_MARKER),
            ),
            ("human", "{question}"),
        ])
        self._chain = prompt | llm | StrOutputParser()

    def ask(self, question: str, context: str) -> AnalysisAnswer:
        try:
            is_personalized = _PERSONALIZATION_MARKER in context
            answer = self._chain.invoke({"context": context, "question": question})
            in_scope = _OUT_OF_SCOPE_MARKER not in answer
            return AnalysisAnswer(answer=answer, in_scope=in_scope, is_personalized=is_personalized)
        except Exception as e:
            return AnalysisAnswer(answer=f"분석 중 오류가 발생했습니다: {e}", in_scope=False)
