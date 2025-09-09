#!/bin/bash

# 프로젝트 경로 설정 (실제 경로로 변경 필요)
PROJECT_PATH="/mnt/d/16.Dev/gemini"
PYTHON_PATH="$PROJECT_PATH/venv/bin/python"

# crontab에 추가할 작업들
echo "# 업무관리시스템 알림 스케줄" > /tmp/gemini_cron
echo "# 매일 오전 9시에 마감일 알림 체크" >> /tmp/gemini_cron
echo "0 9 * * * cd $PROJECT_PATH && $PYTHON_PATH manage.py check_notifications --type=due_date" >> /tmp/gemini_cron
echo "" >> /tmp/gemini_cron
echo "# 매주 금요일 오후 5시에 워크로그 알림 체크" >> /tmp/gemini_cron
echo "0 17 * * 5 cd $PROJECT_PATH && $PYTHON_PATH manage.py check_notifications --type=worklog" >> /tmp/gemini_cron

# 기존 crontab 백업
crontab -l > /tmp/current_cron 2>/dev/null || true

# 새 작업 추가
cat /tmp/current_cron /tmp/gemini_cron | crontab -

echo "Cron 작업이 추가되었습니다."
echo "현재 crontab 내용:"
crontab -l
