import logging
import os
from typing import Dict, Any, List, Optional, Sequence, Iterable
import datetime
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils.html import strip_tags
from worklog.models import Worklog
from reports.models import ReportReview, TeamPerformanceAnalysis, WeeklyReport
from teams.models import Team
from common.gemini_utils import (
    get_gemini_client,
    get_gemini_generation_config,
    get_handled_exceptions,
    extract_gemini_text,
    generate_gemini_content
)

try:
    from google import genai
except ImportError:
    genai = None

try:
    from google.api_core import exceptions as google_exceptions
except ImportError:
    google_exceptions = None

logger = logging.getLogger(__name__)

class TeamPerformanceAnalyzer:
    def __init__(self, team_id: int):
        self.team = Team.objects.get(id=team_id)
        self.model_name = settings.GEMINI_MODEL_NAME
        
        # Configure Gemini
        self.client = get_gemini_client()
        if not self.client:
             raise ValueError("Failed to initialize Gemini client")

    def analyze_last_4_weeks(self, anchor_year: Optional[int] = None, anchor_week: Optional[int] = None) -> Dict[str, Any]:
        """최근 4주간의 데이터를 분석합니다."""
        logger.info(f"Starting performance analysis for team: {self.team.name}")
        
        # 1. 데이터 수집
        data = self._collect_data(anchor_year=anchor_year, anchor_week=anchor_week)
        if not data['member_data']:
            logger.warning("No data found for analysis")
            return {"error": "분석할 데이터가 없습니다."}

        # 2. 프롬프트 구성
        prompt = self._construct_prompt(data)

        # 3. Gemini 호출
        try:
            config = get_gemini_generation_config(temperature=0.2)
            response = generate_gemini_content(
                client=self.client,
                model=self.model_name, 
                contents=prompt,
                config=config
            )
            text = extract_gemini_text(response)
            if not text:
                 return {"error": "AI로부터 응답을 받지 못했습니다."}
            analysis_json = self._parse_response(text)
        except Exception as e:
            logger.error(f"Gemini API Error: {e}", exc_info=True)
            return {"error": str(e)}

        # 4. 결과 저장
        start_week_str = f"{data['weeks'][-1]['year']}-W{data['weeks'][-1]['week']}" # 4주 전 (오래된 순)
        end_week_str = f"{data['weeks'][0]['year']}-W{data['weeks'][0]['week']}"   # 최근 주
        
        analysis_record = TeamPerformanceAnalysis.objects.create(
            team=self.team,
            start_week=start_week_str,
            end_week=end_week_str,
            analysis_data=analysis_json
        )
        
        return analysis_json

    def _clean_html(self, text: Optional[str]) -> str:
        if not text:
            return ""
        import re
        import html
        # 줄바꿈 태그를 실제 개행문자로 변환
        text = re.sub(r'<(?:br|/p|/div)>', '\n', text, flags=re.IGNORECASE)
        # 나머지 태그 제거 및 HTML 엔티티 복원
        text = strip_tags(text)
        text = html.unescape(text)
        # 가독성을 위해 연속된 개행은 하나로 줄임
        text = re.sub(r'\n\s*\n+', '\n', text)
        return text.strip()

    def _collect_data(self, anchor_year: Optional[int] = None, anchor_week: Optional[int] = None) -> Dict[str, Any]:
        """최근 4주 데이터를 수집합니다."""
        if anchor_year and anchor_week:
            anchor_monday = datetime.date.fromisocalendar(anchor_year, anchor_week, 1)
        else:
            today = datetime.date.today()
            anchor_monday = today - datetime.timedelta(days=today.weekday())
        
        # 최근 4주 주차 계산
        target_weeks = []
        for i in range(4):
            d = anchor_monday - datetime.timedelta(weeks=i)
            y, w, _ = d.isocalendar()
            target_weeks.append({'year': y, 'week': w})
        
        member_data = {}
        team_memberships = self.team.teammembership_set.exclude(role='leader').select_related('user__profile')
        team_members = [membership.user for membership in team_memberships]

        for member in team_members:
            member_name = member.profile.get_korean_name if hasattr(member, 'profile') else member.username
            weeks_data = []
            
            for week_info in target_weeks:
                # 워크로그 조회
                worklog = Worklog.objects.filter(
                    author=member,
                    year=week_info['year'],
                    week_number=week_info['week']
                ).first()
                
                # AI 리뷰 조회 (요약만 사용)
                review = ReportReview.objects.filter(
                    user=member,
                    year=week_info['year'],
                    week_number=week_info['week']
                ).values('review_content').first()
                
                week_entry = {
                    "week": f"{week_info['year']}-W{week_info['week']}",
                    "work_done": self._clean_html(worklog.this_week_work) if worklog else "작성 안 함",
                    "next_plan": self._clean_html(worklog.next_week_plan) if worklog else "작성 안 함",
                    "review_summary": self._clean_html(review['review_content'].get('summary')) if review and review.get('review_content') and review['review_content'].get('summary') else ""
                }
                weeks_data.append(week_entry)
            
            # 주차 역순 (과거 -> 현재) 정렬을 위해 뒤집기
            weeks_data.reverse()
            
            member_data[member_name] = weeks_data

        return {
            "weeks": target_weeks, # Note: This is current -> past order
            "member_data": member_data
        }

    def _construct_prompt(self, data: Dict[str, Any]) -> str:
        import json
        
        member_json_str = json.dumps(data['member_data'], ensure_ascii=False, indent=2)
        
        prompt = f"""
당신은 IT 프로젝트 매니저이자 인사 분석 전문가입니다.
다음 JSON 데이터는 '{self.team.name}' 팀원들의 최근 4주간 주간업무보고(실적 및 계획) 내역입니다.

[데이터]\n{member_json_str}\n

[지시사항]
1. 각 담당자별로 주요 수행 업무를 추출하고, 업무의 성격(개발, 기획, 유지보수 등)과 난이도를 평가하세요.
2. 4주간의 흐름을 분석하여 '계획 준수율', '업무 처리 속도', '이슈 해결 능력'을 평가하세요.
3. 각 담당자의 업무 스타일(예: 꼼꼼함, 속도중심, 도전적 등)과 강점/약점을 도출하세요.
4. 팀 전체 관점에서 구성원들의 역량을 비교 분석하고, 최적인 업무 배분 제안을 포함하세요.

[출력 형식]
반드시 다음 JSON 포맷으로만 응답하세요. 마크다운 코드 블록(```json)을 사용하지 마세요.

{{
    "analysis_period": "{datetime.date.today().strftime('%Y-%m-%d')} 기준 최근 4주",
    "team_summary": "팀 전체 종합 평가 및 특징 (3-4문장)",
    "member_analysis": [
        {{
            "name": "담당자명",
            "role_type": "추정되는 주요 역할 (예: 백엔드 개발)",
            "performance_score": 85, 
            "key_tasks": [
                {{"name": "주요업무명", "status": "Completed/Delayed/Ongoing", "complexity": "High/Medium/Low"}}
            ],
            "strengths": ["강점1", "강점2"],
            "weaknesses": ["약점1", "약점2"],
            "work_style": "업무 스타일 설명",
            "consistency": "High/Medium/Low"
        }}
    ],
    "team_recommendation": "팀 차원의 개선 제안 또는 업무 배분 제안"
}}
"""
        return prompt

    def _parse_response(self, text: str) -> Dict[str, Any]:
        import json
        import re
        
        # Clean up code blocks if present
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'^```\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Fallback: try to find JSON object
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise ValueError(f"Invalid JSON response: {text[:100]}...")

# _extract_text removed (moved to common.gemini_utils)



# _resolve_api_key removed (moved to common.gemini_utils)
