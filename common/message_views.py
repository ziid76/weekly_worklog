
import requests
import json
import os

# --- 설정 변수 ---
BASE_URL = "https://api.kakaowork.com/v1"
# 중요: 실제 운영 환경에서는 API 토큰을 코드에 직접 하드코딩하지 않는 것이 좋습니다.
# 환경 변수나 별도의 설정 파일을 사용하는 것을 권장합니다.
BEARER_TOKEN = "ee849873.7ca4173b8adb45d9b3d6e284200a4798"
# BEARER_TOKEN = os.getenv("KAKAOWORK_TOKEN") 

# --- API 요청 헤더 ---
HEADERS = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "Content-Type": "application/json"
}

DEBUG_MODE = os.getenv("DEBUG", "0") == "1"

VERIFY_OPTION = False # if DEBUG_MODE else True


def find_user_id_by_email(email: str) -> int | None:
    """
    이메일 주소를 사용하여 카카오워크 사용자 ID를 조회합니다.

    Args:
        email (str): 조회할 사용자의 이메일 주소.

    Returns:
        int | None: 성공 시 사용자의 고유 ID, 실패 시 None.
    """
    api_url = f"{BASE_URL}/users.find_by_email"
    params = {'email': email}
    
    try:
        response = requests.get(api_url, headers=HEADERS, params=params, verify=VERIFY_OPTION)
        response.raise_for_status()  # HTTP 오류 발생 시 예외를 발생시킴

        response_data = response.json()
        if response_data.get('success') and response_data.get('user'):
            user_id = response_data['user']['id']
            print(f"사용자 ID를 찾았습니다: {user_id}")
            return user_id
        else:
            print(f"오류: 사용자를 찾을 수 없습니다. 응답: {response_data.get('error')}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"API 요청 중 오류가 발생했습니다: {e}")
        return None

def open_conversation(user_id: int) -> int | None:
    """
    사용자 ID를 사용하여 1:1 대화방을 열고 대화방 ID를 반환합니다.

    Args:
        user_id (int): 대화방을 열 대상의 사용자 ID.

    Returns:
        int | None: 성공 시 대화방의 고유 ID, 실패 시 None.
    """
    api_url = f"{BASE_URL}/conversations.open"
    payload = {'user_id': user_id}
    
    try:
        response = requests.post(api_url, headers=HEADERS, data=json.dumps(payload), verify=VERIFY_OPTION)
        response.raise_for_status()

        response_data = response.json()
        if response_data.get('success') and response_data.get('conversation'):
            conversation_id = response_data['conversation']['id']
            print(f"대화방을 생성했습니다: {conversation_id}")
            return conversation_id
        else:
            print(f"오류: 대화방을 열 수 없습니다. 응답: {response_data.get('error')}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"API 요청 중 오류가 발생했습니다: {e}")
        return None

def send_simple_message(conversation_id: int, text: str):
    """
    지정된 대화방으로 텍스트 메시지를 전송합니다.

    Args:
        conversation_id (int): 메시지를 보낼 대화방의 ID.
        text (str): 전송할 메시지의 내용.
    """
    api_url = f"{BASE_URL}/messages.send"
    # 카카오워크 메시지 형식에 맞게 payload 구성
    # 더 복잡한 메시지(블록)를 보내려면 'blocks' 필드를 사용해야 합니다.
    payload = {
        'conversation_id': conversation_id,
        'text': text
    }
    
    try:
        response = requests.post(api_url, headers=HEADERS, data=json.dumps(payload), verify=VERIFY_OPTION)
        response.raise_for_status()

        response_data = response.json()
        if response_data.get('success'):
            print("메시지를 성공적으로 전송했습니다.")
        else:
            print(f"오류: 메시지 전송에 실패했습니다. 응답: {response_data.get('error')}")

    except requests.exceptions.RequestException as e:
        print(f"API 요청 중 오류가 발생했습니다: {e}")


def send_message(conversation_id: int, 
                 text: str,
                 message_type: str = "text",
                 button_text: str = None,
                 button_url: str = None ):
    """
    카카오워크 대화방으로 메시지를 전송합니다.

    Args:
        conversation_id (int): 메시지를 보낼 대화방의 ID
        text (str): 전송할 메시지 내용
        message_type (str): 'text' (일반 메시지) 또는 'box' (메시지 박스)
        button_text (str): 버튼에 표시할 텍스트 (box 모드에서만 사용)
        button_url (str): 버튼 클릭 시 이동할 URL (box 모드에서만 사용)
    """
    api_url = f"{BASE_URL}/messages.send"

    if message_type == "box":
        payload = {
            "conversation_id": conversation_id,
            "text": text,  # 카카오워크에서 기본적으로 필요한 text 필드
            "blocks": []
        }

        # 이미지 블록 추가 (옵션)
        payload["blocks"].append({
            "type": "image_link",
            "url": "https://github.com/ziid76/search/blob/main/itms_msg.png?raw=true",
        })
        payload["blocks"].append({
            "type": "text",
            "text": text
        })

        # 버튼 블록 추가 (옵션)
        if button_text and button_url:
            payload["blocks"].append({
                "type": "button",
                "text": button_text,
                "style": "default",
                "action": {
                    "type": "open_system_browser",
                    "value": button_url
                }
            })
    else:
        # 일반 텍스트 메시지
        payload = {
            "conversation_id": conversation_id,
            "text": text
        }

    try:
        response = requests.post(api_url, headers=HEADERS, data=json.dumps(payload), verify=VERIFY_OPTION)
        response.raise_for_status()

        response_data = response.json()
        if response_data.get("success"):
            print("메시지를 성공적으로 전송했습니다.")
        else:
            print(f"오류: 메시지 전송에 실패했습니다. 응답: {response_data.get('error')}")

    except requests.exceptions.RequestException as e:
        print(f"API 요청 중 오류가 발생했습니다: {e}")



# --- 메인 실행 블록 (예제) ---
if __name__ == "__main__":
    # 1. 이메일로 사용자 ID 찾기
    target_email = "230004@samchully.co.kr"
    user_id = find_user_id_by_email(target_email)

    if user_id:
        # 2. 찾은 사용자 ID로 대화방 열기
        conversation_id = open_conversation(user_id)

        if conversation_id:
            # 3. 열린 대화방으로 메시지 보내기
            message_text = "대화방 생성 후 메시지 전달"
            send_simple_message(conversation_id, message_text)
            # 1) 일반 텍스트 메시지 보내기
            send_message(conversation_id, "이것은 일반 텍스트 메시지입니다.", message_type="text")

            # 2) 메시지 박스 보내기
            send_message(
                conversation_id,
                text="이제 구글 캘린더 Bot으로 보다 똑똑하게, 캘린더 기능을 이용해보세요.",
                message_type="box",
                button_text="설정하기",
                button_url="http://example.com/details/999",
            )

def send_kakao_message(
                 email, 
                 text,
                 message_type,
                 button_text,
                 button_url):
    user_id = find_user_id_by_email(email)
    if user_id:
        conversation_id = open_conversation(user_id)    
        if conversation_id:
            send_message(conversation_id, text, message_type, button_text, button_url)
        else : return False
    
    else : return False
    return True

