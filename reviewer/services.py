import os
import logging
from django.conf import settings
from common.gemini_utils import get_gemini_client, get_gemini_generation_config, generate_gemini_content, extract_gemini_text

logger = logging.getLogger(__name__)

def get_review_prompt():
    """Project root의 review.prompt 파일을 읽어옵니다."""
    prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'review.prompt')
    if not os.path.exists(prompt_path):
        logger.error(f"Prompt file not found at {prompt_path}")
        return ""
    
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.exception(f"Failed to read prompt file: {e}")
        return ""

def perform_code_review(input_code, business_context="", core_review_point=""):
    """LLM을 사용하여 코드 리뷰를 진행합니다."""
    system_prompt = get_review_prompt()
    
    # 프롬프트 조립
    # review.prompt 내부의 # Input Code, # Business Context, # Core Review Point 섹션을 채워넣거나
    # 단순히 뒤에 덧붙이는 방식을 사용할 수 있습니다.
    # 여기서는 섹션 구분자 뒤에 내용을 추가하는 방식을 사용합니다.
    
    full_prompt = system_prompt
    if "# Input Code" in full_prompt:
        full_prompt = full_prompt.replace("# Input Code", f"# Input Code\n{input_code}")
    else:
        full_prompt += f"\n\n# Input Code\n{input_code}"
        
    if business_context:
        if "# Business Context" in full_prompt:
            full_prompt = full_prompt.replace("# Business Context", f"# Business Context\n{business_context}")
        else:
            full_prompt += f"\n\n# Business Context\n{business_context}"
            
    if core_review_point:
        if "# Core Review Point" in full_prompt:
            full_prompt = full_prompt.replace("# Core Review Point", f"# Core Review Point\n{core_review_point}")
        else:
            full_prompt += f"\n\n# Core Review Point\n{core_review_point}"

    client = get_gemini_client()
    if not client:
        return "Error: Gemini client could not be initialized. Please check GEMINI_API_KEY."

    model_name = getattr(settings, 'GEMINI_MODEL_NAME', 'gemini-1.5-pro')
    config = get_gemini_generation_config(response_mime_type="text/plain") # Markdown 결과를 받기 위해 text/plain 사용

    try:
        response = generate_gemini_content(
            client=client,
            model=model_name,
            contents=full_prompt,
            config=config
        )
        return extract_gemini_text(response)
    except Exception as e:
        logger.error(f"Error during Gemini code review: {e}")
        return f"Error: {str(e)}"
