import json
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from app.services import report_review
from worklog.models import Worklog


class ReviewLast4WeeksServiceTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username="alice", password="secret")
        self.anchor = date(2024, 6, 28)  # Friday of ISO week 26

    def _seed_worklogs(self) -> None:
        start_monday = self.anchor - timedelta(days=self.anchor.weekday())
        for offset in range(5):  # create five weeks, latest four should be used
            week_start = start_monday - timedelta(weeks=offset)
            iso_year, iso_week, _ = week_start.isocalendar()
            Worklog.objects.create(
                author=self.user,
                year=iso_year,
                week_number=iso_week,
                this_week_work=f"성과 {iso_week}",
                next_week_plan=f"계획 {iso_week}",
            )

    def _configure_genai(self, mock_genai: MagicMock) -> MagicMock:
        client_instance = MagicMock()
        mock_genai.Client.return_value = client_instance
        mock_genai.types = SimpleNamespace(
            GenerationConfig=MagicMock(return_value="generation-config"),
            RequestOptions=MagicMock(return_value="request-options"),
        )
        return client_instance

    @patch("app.services.report_review._resolve_api_key", return_value="dummy")
    @patch("app.services.report_review.genai")
    def test_collects_last_four_weeks(self, mock_genai: MagicMock, _mock_key: MagicMock) -> None:
        self._seed_worklogs()
        client_instance = self._configure_genai(mock_genai)
        payload = {"summary": "ok", "metrics": {}, "mismatches": [], "risks": [], "recommendations": []}
        response = MagicMock(text=json.dumps(payload))
        client_instance.models.generate_content.return_value = response

        result = report_review.review_last_4_weeks(self.user, as_of=self.anchor)
        self.assertEqual(result, payload)

        call_kwargs = client_instance.models.generate_content.call_args.kwargs
        prompt = call_kwargs["contents"][0]["parts"][0]
        self.assertIn("### 2024년 26주차", prompt)
        self.assertIn("### 2024년 25주차", prompt)
        self.assertIn("### 2024년 24주차", prompt)
        self.assertIn("### 2024년 23주차", prompt)
        self.assertNotIn("### 2024년 22주차", prompt)

    @patch("app.services.report_review._resolve_api_key", return_value="dummy")
    @patch("app.services.report_review.genai")
    def test_prompt_snapshot(self, mock_genai: MagicMock, _mock_key: MagicMock) -> None:
        self._seed_worklogs()
        client_instance = self._configure_genai(mock_genai)
        payload = {"summary": "ok", "metrics": {}, "mismatches": [], "risks": [], "recommendations": []}
        client_instance.models.generate_content.return_value = MagicMock(text=json.dumps(payload))

        report_review.review_last_4_weeks(self.user, as_of=self.anchor)
        prompt = client_instance.models.generate_content.call_args.kwargs["contents"][0]["parts"][0]

        expected = "\n".join(
            [
                "분석 대상자: alice (alice)",
                "요약 기간: 최근 4주 (최신 주 포함)",
                "각 주차는 금주 실적과 차주 계획으로 구성되어 있습니다.",
                "작성 공백은 '미작성'으로 표시했습니다.",
                "",
                "### 2024년 23주차 (2024-06-03 ~ 2024-06-09)",
                "- 금주 실적:",
                "성과 23",
                "- 차주 계획:",
                "계획 23",
                "",
                "### 2024년 24주차 (2024-06-10 ~ 2024-06-16)",
                "- 금주 실적:",
                "성과 24",
                "- 차주 계획:",
                "계획 24",
                "",
                "### 2024년 25주차 (2024-06-17 ~ 2024-06-23)",
                "- 금주 실적:",
                "성과 25",
                "- 차주 계획:",
                "계획 25",
                "",
                "### 2024년 26주차 (2024-06-24 ~ 2024-06-30)",
                "- 금주 실적:",
                "성과 26",
                "- 차주 계획:",
                "계획 26",
                "",
                "분석 지시:",
                "1. 4주 흐름을 살펴 금주 실적 대비 차주 계획의 연계성과 정합성을 평가하세요.",
                "2. 누락된 계획, 반복 지연, 근거 부족, 리스크 징후를 찾아주세요.",
                "3. 제공된 출력 스키마에 맞춰 JSON으로만 응답하세요.",
                "4. 모든 수치 필드에는 숫자 자료를 채워주세요. 데이터 없으면 0으로 입력하세요.",
                "5. 권고 사항은 실행 가능한 행동으로 제시하세요.",
            ]
        )
        self.assertEqual(prompt, expected)

    @patch("app.services.report_review._resolve_api_key", return_value="dummy")
    @patch("app.services.report_review.genai")
    def test_handles_sdk_exception(self, mock_genai: MagicMock, _mock_key: MagicMock) -> None:
        self._configure_genai(mock_genai)
        mock_genai.Client.return_value.models.generate_content.side_effect = TimeoutError("timeout")

        result = report_review.review_last_4_weeks(self.user, as_of=self.anchor)
        self.assertEqual(result["summary"], "AI 점검실패")
        self.assertEqual(result["error"], "timeout")

    @patch("app.services.report_review._resolve_api_key", return_value="dummy")
    @patch("app.services.report_review.genai")
    def test_handles_malformed_json(self, mock_genai: MagicMock, _mock_key: MagicMock) -> None:
        client_instance = self._configure_genai(mock_genai)
        client_instance.models.generate_content.return_value = MagicMock(text="{not-json}")

        result = report_review.review_last_4_weeks(self.user, as_of=self.anchor)
        self.assertEqual(result["summary"], "AI 점검실패")
        self.assertEqual(result["error"], "malformed_json")
        self.assertIn("raw", result)
