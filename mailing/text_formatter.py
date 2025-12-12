"""Text formatting utilities for email content."""

import re
from typing import Any, Dict, List


def format_review_content(review_content: Dict[str, Any]) -> Dict[str, Any]:
    """
    리뷰 내용의 텍스트를 가독성 있게 포맷팅합니다.
    
    Args:
        review_content: AI 리뷰 결과 딕셔너리
        
    Returns:
        포맷팅된 리뷰 내용 딕셔너리
    """
    formatted_content = review_content.copy()
    
    # 요약 텍스트 포맷팅
    if 'summary' in formatted_content:
        formatted_content['summary'] = format_text_content(formatted_content['summary'])
    
    # 권고사항 포맷팅
    if 'recommendations' in formatted_content:
        formatted_content['recommendations'] = [
            format_text_content(item) for item in formatted_content['recommendations']
        ]
    
    # 불일치 항목 포맷팅
    if 'mismatches' in formatted_content:
        for mismatch in formatted_content['mismatches']:
            if 'plan_item' in mismatch:
                mismatch['plan_item'] = format_text_content(mismatch['plan_item'])
            if 'issue' in mismatch:
                mismatch['issue'] = format_text_content(mismatch['issue'])
    
    # 리스크 항목 포맷팅
    if 'risks' in formatted_content:
        for risk in formatted_content['risks']:
            if 'description' in risk:
                risk['description'] = format_text_content(risk['description'])
            if 'next_action' in risk:
                risk['next_action'] = format_text_content(risk['next_action'])
    
    return formatted_content


def format_text_content(text: str) -> str:
    """
    텍스트 내용을 가독성 있게 포맷팅합니다.
    
    Args:
        text: 원본 텍스트
        
    Returns:
        포맷팅된 텍스트
    """
    if not text or not isinstance(text, str):
        return text
    
    # 기본 정리
    formatted_text = text.strip()
    
    # 연속된 공백을 하나로 통합
    formatted_text = re.sub(r'\s+', ' ', formatted_text)
    
    # 문장 끝 마침표 후 적절한 줄바꿈 추가
    formatted_text = re.sub(r'\.(\s*)([A-Z가-힣])', r'.\n\n\2', formatted_text)
    
    # 콜론 뒤 줄바꿈 처리 (목록 형태)
    formatted_text = re.sub(r':(\s*)([•\-\*])', r':\n\2', formatted_text)
    
    # 번호 목록 앞에 줄바꿈 추가
    formatted_text = re.sub(r'(\.)(\s*)(\d+\.)', r'\1\n\n\3', formatted_text)
    
    # 불필요한 연속 줄바꿈 정리
    formatted_text = re.sub(r'\n{3,}', '\n\n', formatted_text)
    
    return formatted_text.strip()


def add_bullet_points(items: List[str]) -> List[str]:
    """
    리스트 항목에 불릿 포인트를 추가합니다.
    
    Args:
        items: 원본 항목 리스트
        
    Returns:
        불릿 포인트가 추가된 항목 리스트
    """
    formatted_items = []
    for item in items:
        if not item.strip().startswith(('•', '-', '*', '▪', '▫')):
            formatted_items.append(f"• {item.strip()}")
        else:
            formatted_items.append(item.strip())
    return formatted_items


def format_metrics_details(details: List[str]) -> List[str]:
    """
    메트릭 상세 정보를 포맷팅합니다.
    
    Args:
        details: 원본 상세 정보 리스트
        
    Returns:
        포맷팅된 상세 정보 리스트
    """
    if not details:
        return []
    
    formatted_details = []
    for detail in details:
        if detail and isinstance(detail, str):
            # 각 항목을 간결하게 정리
            formatted_detail = detail.strip()
            if formatted_detail and not formatted_detail.startswith(('•', '-', '*')):
                formatted_detail = f"• {formatted_detail}"
            formatted_details.append(formatted_detail)
    
    return formatted_details
