#!/usr/bin/env python
import os
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from common.message_views import send_kakao_message

def test_kakao_notification():
    """카카오톡 알림 테스트"""
    test_email = "230004@samchully.co.kr"  # 테스트할 이메일 주소
    
    message = """📋 새 업무가 할당되었습니다

제목: 테스트 업무
할당자: 관리자
우선순위: 높음"""
    
    result = send_kakao_message(
        email=test_email,
        text=message,
        message_type="box",
        button_text="업무 확인하기",
        button_url="http://itms.samchully.co.kr/task/1/"
    )
    
    if result:
        print("✅ 카카오톡 알림 전송 성공")
    else:
        print("❌ 카카오톡 알림 전송 실패")

if __name__ == "__main__":
    test_kakao_notification()
