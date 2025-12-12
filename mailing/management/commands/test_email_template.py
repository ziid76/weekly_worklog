from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import User
import json


class Command(BaseCommand):
    help = 'Test email template with sample data'

    def handle(self, *args, **options):
        """이메일 템플릿을 샘플 데이터로 테스트합니다."""
        
        # 샘플 리뷰 데이터
        sample_review = {
            "summary": "4주간의 업무 분석 결과, 전반적으로 계획 대비 실적이 양호하나 일부 항목에서 지연이 발생했습니다. 특히 API 개발 부분에서 예상보다 시간이 소요되었으며, 테스트 단계에서 추가 이슈가 발견되었습니다. 다음 주부터는 더욱 구체적인 일정 관리가 필요합니다.",
            "metrics": {
                "planned_count": {"value": 12, "details": ["API 개발", "UI 구현", "테스트 작성", "문서화"]},
                "done_count": {"value": 9, "details": ["API 기본 구조", "메인 UI", "단위 테스트"]},
                "completion_rate": {"value": 75.0, "details": ["계획 12개 중 9개 완료"]},
                "avg_delay_days": {"value": 2.5, "details": ["API 개발 3일 지연", "테스트 2일 지연"]},
                "carryover_count": {"value": 3, "details": ["API 최적화", "통합 테스트", "성능 개선"]},
                "missing_evidence_count": {"value": 1, "details": ["성능 테스트 결과 누락"]}
            },
            "recommendations": [
                "API 개발 시 더 세분화된 단위로 작업을 나누어 진행 상황을 명확히 파악하시기 바랍니다.",
                "테스트 단계에서 발견되는 이슈를 줄이기 위해 개발 중간중간 코드 리뷰를 진행하는 것을 권장합니다.",
                "성능 관련 작업은 별도의 시간을 할당하여 충분한 검증을 거치시기 바랍니다."
            ],
            "mismatches": [
                {
                    "plan_item": "사용자 인증 API 완료",
                    "issue": "계획된 완료일보다 3일 지연되었으며, 보안 검토 단계에서 추가 수정이 필요한 상황입니다.",
                    "evidence_needed": ["보안 검토 결과서", "수정 완료 확인서"]
                },
                {
                    "plan_item": "성능 최적화 작업",
                    "issue": "구체적인 성능 지표나 개선 결과가 명시되지 않아 실제 완료 여부를 판단하기 어렵습니다.",
                    "evidence_needed": ["성능 테스트 결과", "Before/After 비교 데이터"]
                }
            ],
            "risks": [
                {
                    "description": "API 개발 지연으로 인한 전체 프로젝트 일정 영향",
                    "status": "악화",
                    "owner": "개발팀",
                    "next_action": "추가 개발자 투입 검토 및 우선순위 재조정 필요. 핵심 기능 먼저 완료 후 부가 기능은 다음 스프린트로 이연 고려",
                    "due": "2024-11-25"
                },
                {
                    "description": "테스트 커버리지 부족으로 인한 품질 리스크",
                    "status": "지속",
                    "owner": "QA팀",
                    "next_action": "자동화 테스트 도구 도입 및 테스트 케이스 보강",
                    "due": "2024-11-30"
                }
            ],
            "error": None
        }
        
        # 테스트용 사용자 (첫 번째 사용자 사용)
        try:
            user = User.objects.first()
            if not user:
                self.stdout.write(self.style.ERROR("테스트할 사용자가 없습니다. 먼저 사용자를 생성해주세요."))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"사용자 조회 중 오류: {e}"))
            return
        
        context = {
            'review': sample_review,
            'user': user,
            'year': 2024,
            'week_number': 47,
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        }
        
        try:
            # HTML 템플릿 렌더링
            html_content = render_to_string('emails/review_notification.html', context)
            
            # 결과를 파일로 저장
            output_file = 'email_preview.html'
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.stdout.write(self.style.SUCCESS(f"✅ 이메일 템플릿이 성공적으로 생성되었습니다: {output_file}"))
            self.stdout.write(f"브라우저에서 {output_file}을 열어 결과를 확인하세요.")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ 템플릿 렌더링 중 오류 발생: {e}"))
            import traceback
            traceback.print_exc()
