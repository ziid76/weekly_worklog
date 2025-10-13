"""AI review service for weekly reports."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Dict, Iterable, List, Optional, Sequence

from django.conf import settings
from django.contrib.auth import get_user_model

from worklog.models import Worklog

from google import genai
from google.api_core import exceptions as google_exceptions



User = get_user_model()
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WeekWindow:
    """Container for a single ISO week slice."""

    year: int
    week_number: int
    week_start: date


def review_last_4_weeks(user: User, as_of: Optional[date] = None) -> Dict[str, Any]:
    """Run Gemini-based audit for the user's latest four weeks of worklogs.

    Args:
        user: Authenticated user requesting their own report review.
        as_of: Optional anchor date; defaults to today when omitted.

    Returns:
        Parsed JSON dictionary produced by Gemini. Falls back to a guarded
        structure when the API is unavailable or the response cannot be parsed.
    """

    anchor = as_of or date.today()
    weeks = _compute_weeks(anchor)
    entries = _collect_worklogs(user, weeks)
    logger.debug("Collected %s weeks for review", len(entries))

    prompt = _build_prompt(user, entries, anchor)
    logger.debug("Generated prompt length=%s", len(prompt))

    api_key = _resolve_api_key()
    if not api_key:
        logger.error("Gemini API key is not configured")
        return _fallback_result("API key not configured")

    if not genai:  # pragma: no cover - depends on optional dependency
        logger.error("google-genai package is not installed")
        return _fallback_result("google-genai package not installed")

    client = genai.Client(api_key=api_key)
    model_name = getattr(settings, "GEMINI_MODEL_NAME", "gemini-pro")
    timeout_seconds = getattr(settings, "GEMINI_TIMEOUT", 30)

    full_prompt = f"{_system_instruction()}\n\n{prompt}"

    try:
        logger.info("Requesting Gemini review for user=%s model=%s", user.pk, model_name)
        response = client.models.generate_content(
            model=model_name,
            contents=full_prompt,
            config=_generation_config(),
        )
    except tuple(_handled_exceptions()) as exc:  # type: ignore[arg-type]
        logger.exception("Gemini request failed: %s", exc)
        return _fallback_result(str(exc))
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Unexpected Gemini error: %s", exc)
        return _fallback_result("unexpected_error")

    raw_text = _extract_text(response)
    if not raw_text:
        logger.error("Gemini response missing text payload")
        return _fallback_result("empty_response")

    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        logger.exception("Malformed JSON from Gemini: %s", exc)
        fallback = _fallback_result("malformed_json")
        fallback["raw"] = raw_text
        return fallback

    return payload


def _handled_exceptions() -> Sequence[type]:
    handlers: List[type] = [TimeoutError]
    if google_exceptions:
        handlers.append(google_exceptions.GoogleAPIError)
    try:
        from requests import exceptions as requests_exceptions
    except ImportError:  # pragma: no cover - requests bundled with SDK
        requests_exceptions = None
    if requests_exceptions:
        handlers.extend(
            [
                requests_exceptions.Timeout,
                requests_exceptions.ConnectionError,
                requests_exceptions.HTTPError,
            ]
        )
    return tuple(handlers)


def _compute_weeks(anchor: date) -> List[WeekWindow]:
    monday = anchor - timedelta(days=anchor.weekday())
    windows: List[WeekWindow] = []
    for offset in range(3, -1, -1):
        week_start = monday - timedelta(weeks=offset)
        iso_year, iso_week, _ = week_start.isocalendar()
        windows.append(WeekWindow(year=iso_year, week_number=iso_week, week_start=week_start))
    return windows


def _collect_worklogs(user: User, windows: Iterable[WeekWindow]) -> List[Dict[str, Any]]:
    window_list = list(windows)
    years = {window.year for window in window_list}
    week_numbers = {window.week_number for window in window_list}

    queryset = (
        Worklog.objects.filter(author=user, year__in=years, week_number__in=week_numbers)
        .only("year", "week_number", "this_week_work", "next_week_plan")
    )
    worklog_map = {(worklog.year, worklog.week_number): worklog for worklog in queryset}

    entries: List[Dict[str, Any]] = []
    for window in window_list:
        worklog = worklog_map.get((window.year, window.week_number))
        entries.append(
            {
                "year": window.year,
                "week_number": window.week_number,
                "week_start": window.week_start,
                "week_end": window.week_start + timedelta(days=6),
                "this_week_work": (worklog.this_week_work if worklog else ""),
                "next_week_plan": (worklog.next_week_plan if worklog else ""),
                "has_worklog": worklog is not None,
            }
        )
    return entries


def _resolve_api_key() -> Optional[str]:
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def _system_instruction() -> str:
    return (
        "당신은 PMO 보조분석가입니다. 제공되는 4주간의 주간보고(금주 실적/차주 계획)를 기반으로 "
        "정합성, 누락, 지연, 리스크를 점검하고 실질적인 개선 권고를 제시하세요."
    )


def _build_prompt(user: User, entries: Sequence[Dict[str, Any]], anchor_date: date) -> str:
    profile = getattr(user, "profile", None)
    display_name = getattr(profile, "get_korean_name", None)
    if callable(display_name):
        display_name = display_name()
    elif display_name:
        display_name = str(display_name)
    else:
        display_name = user.get_full_name() or user.username

    lines = [
        f"분석 기준일: {anchor_date.isoformat()}",
        "분석 대상자: {name} ({username})".format(name=display_name, username=user.username),
        "요약 기간: 최근 4주 (최신 주 포함)",
        "각 주차는 금주 실적과 차주 계획으로 구성되어 있습니다.",
        "작성 공백은 '미작성'으로 표시했습니다.",
        "",
    ]

    for entry in entries:
        title = (
            f"### {entry['year']}년 {entry['week_number']}주차"
            f" ({entry['week_start'].isoformat()} ~ {entry['week_end'].isoformat()})"
        )
        lines.extend([title])
        if entry["has_worklog"]:
            lines.append("- 금주 실적:")
            lines.append(entry["this_week_work"].strip() or "(내용은 공백이지만 보고서는 존재)")
            lines.append("- 차주 계획:")
            lines.append(entry["next_week_plan"].strip() or "(내용은 공백이지만 계획이 비어있음)")
        else:
            lines.append("- 금주 실적: 미작성")
            lines.append("- 차주 계획: 미작성")
        lines.append("")

    lines.extend(
        [
            "분석 지시:",
            "1. 4주 흐름을 살펴 금주 실적 대비 차주 계획의 연계성과 정합성을 평가하세요.",
            "2. 누락된 계획, 반복 지연, 근거 부족, 리스크 징후를 찾아주세요.",
            "3. 제공된 출력 스키마에 맞춰 JSON으로만 응답하세요.",
            "4. 모든 수치 필드에는 숫자 자료를 채워주세요. 완료율은 100%를 넘길 수 없습니다. 데이터 없으면 0으로 입력하세요.",
            "5. 권고 사항은 실행 가능한 행동으로 제시하세요.",
            "6. 각 'metric' 항목은 'value' (숫자)와 'details' (문자열 배열)을 포함해야 합니다. 'details'에는 해당 지표의 근거가 되는 항목들을 상세한 목록으로 나열하세요.(ex, value=10이면, details에 10개를 목록으로 포함)",
            "7. 'mismatches' 는 중복된 내용을 포함하지 마세요.",
            "8. 'mismatches' 는 지난 주의 계획에 있으나 금주의 실적에는 누락된 항목, 지난 계획의 완료 일정과 실적이 지연되거나 차이가 나는 항목 등을 분석해서 제시하세요.",
        ]
    )

    return "\n".join(lines)


def _request_options(timeout_seconds: int) -> Optional[Any]:
    if timeout_seconds <= 0:
        return None
    if not genai:  # pragma: no cover - handled earlier
        return None

    types_module = getattr(genai, "types", None)
    if types_module:
        request_options_cls = getattr(types_module, "RequestOptions", None)
        if request_options_cls:
            try:
                return request_options_cls(timeout=timeout_seconds)
            except TypeError:  # pragma: no cover - defensive
                pass
        generate_request_cls = getattr(types_module, "GenerateContentRequest", None)
        if generate_request_cls:
            nested = getattr(generate_request_cls, "RequestOptions", None)
            if nested:
                try:
                    return nested(timeout=timeout_seconds)
                except TypeError:  # pragma: no cover - defensive
                    pass
    return {"timeout": timeout_seconds}


def _generation_config() -> Any:
    if not genai:  # pragma: no cover - handled earlier
        return None

    schema = _response_schema()
    # Fallback for unexpected SDK layout    
    return {
        "temperature": 0.2,
        "response_mime_type": "application/json",
        "response_schema": schema,
    }


def _response_schema() -> Dict[str, Any]:
    # Schema for metrics that are counts
    count_metric = {
        "type": "object",
        "properties": {
            "value": {"type": "integer"},
            "details": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["value", "details"],
    }
    # Schema for metrics that are rates or averages
    float_metric = {
        "type": "object",
        "properties": {
            "value": {"type": "number"},
            "details": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["value", "details"],
    }
    return {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "metrics": {
                "type": "object",
                "properties": {
                    "planned_count": count_metric,
                    "done_count": count_metric,
                    "completion_rate": float_metric,
                    "avg_delay_days": float_metric,
                    "carryover_count": count_metric,
                    "missing_evidence_count": count_metric,
                },
                "required": [
                    "planned_count",
                    "done_count",
                    "completion_rate",
                    "avg_delay_days",
                    "carryover_count",
                    "missing_evidence_count",
                ],
            },
            "mismatches": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "plan_item": {"type": "string"},
                        "issue": {"type": "string"},
                        "evidence_needed": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["plan_item", "issue", "evidence_needed"],
                },
            },
            "risks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "status": {
                            "type": "string",
                            "enum": ["지속", "완화", "악화"],
                        },
                        "owner": {"type": "string"},
                        "next_action": {"type": "string"},
                        "due": {"type": "string", "format": "date"},
                    },
                    "required": ["description", "status", "owner", "next_action", "due"],
                },
            },
            "recommendations": {
                "type": "array",
                "items": {"type": "string"},
            },
            "error": {"type": "string"},
        },
        "required": ["summary", "metrics", "mismatches", "risks", "recommendations"],
    }


def _fallback_result(reason: str) -> Dict[str, Any]:
    base = {
        "summary": "AI 점검실패",
        "metrics": {
            "planned_count": {"value": 0, "details": []},
            "done_count": {"value": 0, "details": []},
            "completion_rate": {"value": 0.0, "details": []},
            "avg_delay_days": {"value": 0.0, "details": []},
            "carryover_count": {"value": 0, "details": []},
            "missing_evidence_count": {"value": 0, "details": []},
        },
        "mismatches": [],
        "risks": [],
        "recommendations": [],
        "error": reason,
    }
    return base


def _extract_text(response: Any) -> str:
    text = getattr(response, "text", None)
    if isinstance(text, str) and text.strip():
        return text

    candidates = getattr(response, "candidates", None)
    if candidates:
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            if not content:
                continue
            parts = getattr(content, "parts", None)
            if not parts:
                continue
            texts = [getattr(part, "text", "") for part in parts if getattr(part, "text", "")]
            if texts:
                return "\n".join(texts)
    return ""

def _guide_response_schema() -> Dict[str, Any]:
    """Returns the JSON schema for the writing guide response."""
    item_schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "content": {"type": "string"},
        },
        "required": ["title", "content"],
    }
    return {
        "type": "object",
        "properties": {
            "suggested_this_week_work": {
                "type": "array",
                "items": item_schema,
            },
            "suggested_next_week_plan": {
                "type": "array",
                "items": item_schema,
            },
        },
        "required": ["suggested_this_week_work", "suggested_next_week_plan"],
    }

def _guide_system_instruction() -> str:
    """Returns the system instruction for the writing guide generation."""
    return (
        "당신은 사용자가 주간 업무 보고서를 잘 작성하도록 돕는 유능한 조수입니다. "
        "과거의 보고서 내용을 기반으로, 새로 작성할 보고서에 포함되어야 할 항목을 추천합니다."
    )

def _build_guide_prompt(user: User, worklogs: Sequence[Worklog]) -> str:
    """Builds the prompt for generating the writing guide."""
    profile = getattr(user, "profile", None)
    display_name = getattr(profile, "get_korean_name", None)
    if callable(display_name):
        display_name = display_name()
    elif display_name:
        display_name = str(display_name)
    else:
        display_name = user.get_full_name() or user.username

    lines = [
        f"분석 대상자: {display_name} ({user.username})",
        "분석 대상: 최근에 작성된 최대 4개의 주간 보고서",
        "",
    ]

    if not worklogs:
        lines.append("분석할 이전 주간 보고서가 없습니다.")
    else:
        lines.append("### 이전 주간 보고서 내용 ###")
        for worklog in worklogs:
            title = f"- {worklog.year}년 {worklog.week_number}주차 ({worklog.week_start_date.isoformat()} ~ {worklog.week_end_date.isoformat()})"
            lines.append(title)
            lines.append("  - 금주 실적:")
            lines.append(f"    {worklog.this_week_work.strip() or '(내용 없음)'}")
            lines.append("  - 차주 계획:")
            lines.append(f"    {worklog.next_week_plan.strip() or '(내용 없음)'}")
            lines.append("")

    lines.extend(
        [
            "### 작성 가이드 생성 지시 ###",
            "1. 위에 제공된 '이전 주간 보고서 내용'을 분석하여, 새로 작성할 주간 보고서의 '금주 실적'과 '차주 계획'에 들어갈 내용을 추천해주세요.",
            "2. 각 추천 항목은 'title'과 'content' 필드를 가진 JSON 객체 형태로 반환해야 합니다.",
            "   - 'title'과 'content'는 개조식으로 작성되어야 합니다",
            "   - 'title'은 추천 항목의 핵심 내용을 요약한 짧은 문구입니다. (예: '지난주 계획 이월', '신규 프로젝트 시작')",
            "   - 'content'는 'title'에 대한 상세 설명 또는 구체적인 작성 가이드입니다. ",
            "3. '금주 실적' 추천 항목:",
            "   - 가장 최근 보고서의 '차주 계획'이 이번 주에 잘 이행되었는지 확인하고, 그 결과를 바탕으로 실적 항목을 제안하세요.",
            "   - 여러 주에 걸쳐 계속 언급되는 항목이나 지연된 항목이 있다면, 진행 상황을 보고하도록 제안하세요.",
            "4. '차주 계획' 추천 항목:",
            "   - 분석된 모든 보고서의 흐름을 파악하여, 앞으로 해야 할 논리적인 다음 단계를 '차주 계획'으로 제안하세요.",
            "   - 예를 들어, 'X 개발 완료'가 실적이라면, 'X 테스트 및 배포'를 계획으로 제안할 수 있습니다.",
            "5. 제안하는 각 항목의 'content'는  구체적인 행동 지침이어야 합니다.",
            "6. 제공된 JSON 출력 스키마에 맞춰서만 응답해야 합니다. 다른 설명은 절대 추가하지 마세요.",
            "7. 추천할 내용이 없다면 빈 배열 `[]`을 반환하세요.",
        ]
    )
    return "\n".join(lines)


def generate_writing_guide(user: User) -> Dict[str, Any]:
    """Generate a writing guide for the user's new worklog based on past reports."""
    
    # 1. Collect last 4 worklogs
    worklogs = list(Worklog.objects.filter(author=user).order_by('-year', '-week_number')[:4])
    logger.debug("Collected %s past worklogs for writing guide", len(worklogs))

    # 2. Build the prompt
    prompt = _build_guide_prompt(user, worklogs)
    logger.debug("Generated guide prompt length=%s", len(prompt))

    # 3. Check API key and dependencies
    api_key = _resolve_api_key()
    if not api_key:
        logger.error("Gemini API key is not configured")
        return {"error": "API 키가 설정되지 않았습니다."}

    if not genai:
        logger.error("google-genai package is not installed")
        return {"error": "google-genai 패키지가 설치되지 않았습니다."}

    # 4. Set up Gemini client and call API
    client = genai.Client(api_key=api_key)
    model_name = getattr(settings, "GEMINI_MODEL_NAME", "gemini-pro")
    
    generation_config = {
        "temperature": 0.3,
        "response_mime_type": "application/json",
        "response_schema": _guide_response_schema(),
    }
    
    full_prompt = f"{_guide_system_instruction()}\n\n{prompt}"

    try:
        logger.info("Requesting Gemini writing guide for user=%s", user.pk)
        response = client.models.generate_content(
            model=model_name,
            contents=full_prompt,
            config=generation_config,
        )
    except tuple(_handled_exceptions()) as exc:
        logger.exception("Gemini guide request failed: %s", exc)
        return {"error": f"AI 서비스 요청에 실패했습니다: {exc}"}
    except Exception:
        logger.exception("Unexpected Gemini error for guide request")
        return {"error": "예상치 못한 AI 서비스 오류가 발생했습니다."}

    # 5. Parse and return response
    raw_text = _extract_text(response)
    if not raw_text:
        logger.error("Gemini guide response missing text payload")
        return {"error": "AI로부터 비어 있는 응답을 받았습니다."}

    try:
        payload = json.loads(raw_text)
        # Add report identifiers to the payload for context
        payload['based_on_reports'] = [f"{w.year}-W{w.week_number}" for w in worklogs]
        return payload
    except json.JSONDecodeError:
        logger.exception("Malformed JSON from Gemini for guide: %s", raw_text)
        return {"error": "AI가 잘못된 형식의 응답을 반환했습니다."}

__all__ = ["review_last_4_weeks", "generate_writing_guide"]
