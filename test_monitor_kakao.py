#!/usr/bin/env python
import os
import sys
import django
from datetime import date

# Django 설정
sys.path.append('/mnt/d/16.Dev/gemini')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    django.setup()
    
    from common.message_views import send_kakao_message
    from django.conf import settings
    
    def test_monitor_approval_notification():
        """시스템 점검 승인요청 카카오 알림 테스트"""
        test_email = "230004@samchully.co.kr"  # 팀장 이메일
        
        approval_url = f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/monitor/approval/"
        kakao_message = f"""📋 시스템 일일점검 승인요청
        
날짜: {date.today().strftime('%Y-%m-%d')}
담당자: 테스트 담당자
팀: IT팀

점검이 완료되어 승인을 요청합니다."""
        
        result = send_kakao_message(
            email=test_email,
            text=kakao_message,
            message_type="box",
            button_text="승인 처리하기",
            button_url=approval_url
        )
        
        if result:
            print("✅ 시스템 점검 승인요청 카카오 알림 전송 성공")
        else:
            print("❌ 시스템 점검 승인요청 카카오 알림 전송 실패")
    
    if __name__ == "__main__":
        test_monitor_approval_notification()
        
except Exception as e:
    print(f"오류 발생: {e}")
    # Django shell을 통한 대안 실행
    os.system('''cd /mnt/d/16.Dev/gemini && echo "
from common.message_views import send_kakao_message
from datetime import date
from django.conf import settings

approval_url = f\\"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/monitor/approval/\\"
message = f\\"📋 시스템 일일점검 승인요청\\n\\n날짜: {date.today().strftime('%Y-%m-%d')}\\n담당자: 테스트 담당자\\n팀: IT팀\\n\\n점검이 완료되어 승인을 요청합니다.\\"

result = send_kakao_message(
    email='230004@samchully.co.kr',
    text=message,
    message_type='box',
    button_text='승인 처리하기',
    button_url=approval_url
)
print('시스템 점검 승인요청 카카오 알림 전송 결과:', result)
" | python3 manage.py shell''')
