"""Custom template filters for text formatting in emails."""

from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()


@register.filter
def smart_linebreaks(value):
    """
    텍스트에 스마트한 줄바꿈을 적용합니다.
    기존 linebreaks 필터보다 더 나은 가독성을 제공합니다.
    """
    if not value:
        return value
    
    # 기본 정리
    text = str(value).strip()
    
    # 연속된 공백을 하나로 통합
    text = re.sub(r'\s+', ' ', text)
    
    # 문장 끝 마침표 후 적절한 줄바꿈 추가
    text = re.sub(r'\.(\s*)([A-Z가-힣])', r'.<br><br>\2', text)
    
    # 콜론 뒤 줄바꿈 처리 (목록 형태)
    text = re.sub(r':(\s*)([•\-\*])', r':<br>\2', text)
    
    # 번호 목록 앞에 줄바꿈 추가
    text = re.sub(r'(\.)(\s*)(\d+\.)', r'\1<br><br>\3', text)
    
    # 기본 줄바꿈 처리
    text = text.replace('\n', '<br>')
    
    # 불필요한 연속 <br> 정리
    text = re.sub(r'(<br>\s*){3,}', '<br><br>', text)
    
    return mark_safe(text)


@register.filter
def format_percentage(value):
    """퍼센티지 값을 보기 좋게 포맷팅합니다."""
    try:
        num = float(value)
        if num == int(num):
            return f"{int(num)}%"
        else:
            return f"{num:.1f}%"
    except (ValueError, TypeError):
        return value


@register.filter
def add_bullet(value):
    """텍스트 앞에 불릿 포인트를 추가합니다."""
    if not value:
        return value
    
    text = str(value).strip()
    if not text.startswith(('•', '-', '*', '▪', '▫')):
        return f"• {text}"
    return text


@register.filter
def highlight_keywords(value):
    """중요한 키워드를 강조 표시합니다."""
    if not value:
        return value
    
    text = str(value)
    
    # 중요한 키워드들을 강조
    keywords = [
        '긴급', '지연', '위험', '문제', '이슈', '개선', '권고', '필수', '중요',
        '완료', '성공', '달성', '목표', '계획', '실적'
    ]
    
    for keyword in keywords:
        text = re.sub(
            f'({keyword})',
            r'<strong style="color: #667eea;">\1</strong>',
            text,
            flags=re.IGNORECASE
        )
    
    return mark_safe(text)
