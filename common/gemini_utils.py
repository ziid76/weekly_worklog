import os
import logging
from typing import Any, Dict, Optional, Sequence
from django.conf import settings

try:
    from google import genai
    from google.api_core import exceptions as google_exceptions
except ImportError:
    genai = None
    google_exceptions = None

logger = logging.getLogger(__name__)

def get_gemini_client() -> Optional[Any]:
    """Gemini 클라이언트를 생성하여 반환합니다."""
    if not genai:
        logger.error("google-genai package is not installed")
        return None
    
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.error("Gemini API key is not configured")
        return None
        
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        logger.exception("Failed to initialize Gemini client: %s", e)
        return None

def get_gemini_generation_config(
    response_schema: Optional[Dict[str, Any]] = None,
    temperature: float = 0.2,
    response_mime_type: str = "application/json"
) -> Dict[str, Any]:
    """
    공통 Gemini 생성 설정을 반환합니다.
    최신 3.x 모델에서 thoughtSignature(Thinking)를 제외하도록 설정합니다.
    """
    config = {
        "temperature": temperature,
        "response_mime_type": response_mime_type,
    }
    
    if response_schema:
        config["response_schema"] = response_schema
        
    # 사고 과정(Thinking) 관련 데이터를 응답에 포함하지 않도록 설정
    # 3.x 모델에서 thoughtSignature를 받지 않기 위한 핵심 설정
    config["thinking_config"] = {
        "include_thoughts": False
    }
    
    return config

def get_handled_exceptions() -> Sequence[type]:
    """Gemini 호출 시 처리해야 할 공통 예외 목록을 반환합니다."""
    handlers = [TimeoutError]
    if google_exceptions:
        handlers.append(google_exceptions.GoogleAPIError)
    
    try:
        from requests import exceptions as requests_exceptions
        handlers.extend([
            requests_exceptions.Timeout,
            requests_exceptions.ConnectionError,
            requests_exceptions.HTTPError,
        ])
    except ImportError:
        pass
        
    return tuple(handlers)

def generate_gemini_content(
    client: Any,
    model: str,
    contents: Any,
    config: Dict[str, Any]
) -> Any:
    """
    Gemini API를 호출하고 프롬프트와 응답을 로깅합니다.
    """
    # 프롬프트 로깅 (보안상 민감한 정보가 포함될 수 있으므로 주의가 필요할 수 있음)
    logger.info("--- Gemini Request ---")
    logger.info("Model: %s", model)
    logger.info("Prompt: %s", contents)
    
    try:
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config
        )
        
        # 응답 텍스트 로깅
        response_text = extract_gemini_text(response)
        logger.info("--- Gemini Response ---")
        logger.info("Text: %s", response_text)
        
        return response
    except Exception as e:
        logger.error("--- Gemini Error ---")
        logger.error("Message: %s", str(e))
        raise

def extract_gemini_text(response: Any) -> str:
    """Gemini 응답 객체에서 텍스트를 추출합니다."""
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
