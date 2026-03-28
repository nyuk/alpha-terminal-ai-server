from typing import List

from app.domains.market_video.application.response.noun_frequency_response import (
    NounFrequencyItem,
    NounFrequencyResponse,
    WordCloudItem,
)
from app.domains.market_video.application.usecase.morph_analyzer_port import MorphAnalyzerPort
from app.domains.market_video.application.usecase.video_comment_port import VideoCommentPort
from app.domains.market_video.domain.service.noun_extraction_service import NounExtractionService


class ExtractNounsUseCase:
    def __init__(
        self,
        comment_port: VideoCommentPort,
        morph_port: MorphAnalyzerPort,
    ):
        self._comment_port = comment_port
        self._morph_port = morph_port
        self._service = NounExtractionService()

    def execute(
        self,
        video_ids: List[str],
        order: str = "relevance",
        max_per_video: int = 20,
        top_n: int = 30,
    ) -> NounFrequencyResponse:
        """
        :param video_ids: market_videos 테이블에서 조회한 video_id 목록
        :param order: 댓글 정렬 기준 'relevance' | 'time'
        :param max_per_video: 영상당 최대 수집 댓글 수
        :param top_n: 반환할 상위 명사 수
        """
        if not video_ids:
            return NounFrequencyResponse(keywords=[], word_cloud_data=[], total_noun_count=0, analyzed_video_count=0)

        all_nouns: List[str] = []
        analyzed_count = 0

        for video_id in video_ids:
            comments = self._comment_port.fetch_comments(video_id, order, max_per_video)
            if not comments:
                continue

            analyzed_count += 1
            for comment in comments:
                raw_nouns = self._morph_port.extract_nouns(comment.content)
                all_nouns.extend(self._service.filter_nouns(raw_nouns))

        freq = self._service.count_frequencies(all_nouns)
        top_items = list(freq.items())[:top_n]

        top_keywords = [NounFrequencyItem(noun=noun, count=count) for noun, count in top_items]
        word_cloud_data = [WordCloudItem(text=noun, value=count) for noun, count in top_items]

        return NounFrequencyResponse(
            keywords=top_keywords,
            word_cloud_data=word_cloud_data,
            total_noun_count=len(all_nouns),
            analyzed_video_count=analyzed_count,
        )
