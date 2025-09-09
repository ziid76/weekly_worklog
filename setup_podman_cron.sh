#!/bin/bash

# 컨테이너 이름 설정
CONTAINER_NAME="gemini-app"

# crontab에 추가할 작업들
echo "# 업무관리시스템 알림 스케줄 (Podman)" > /tmp/gemini_podman_cron
echo "# 매일 오전 9시에 마감일 알림 체크" >> /tmp/gemini_podman_cron
echo "0 9 * * * podman exec $CONTAINER_NAME python manage.py check_notifications --type=due_date" >> /tmp/gemini_podman_cron
echo "" >> /tmp/gemini_podman_cron
echo "# 매주 금요일 오후 5시에 워크로그 알림 체크" >> /tmp/gemini_podman_cron
echo "0 17 * * 5 podman exec $CONTAINER_NAME python manage.py check_notifications --type=worklog" >> /tmp/gemini_podman_cron

# 기존 crontab 백업
crontab -l > /tmp/current_cron 2>/dev/null || true

# 새 작업 추가
cat /tmp/current_cron /tmp/gemini_podman_cron | crontab -

echo "Podman Cron 작업이 추가되었습니다."
echo "현재 crontab 내용:"
crontab -l
