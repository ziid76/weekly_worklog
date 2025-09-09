FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y vim && apt-get install -y cron && rm -rf /var/lib/apt/lists/*
COPY . .

# crontab 파일 복사
COPY crontab /etc/cron.d/itms-cron
RUN chmod 0644 /etc/cron.d/itms-cron
RUN crontab /etc/cron.d/itms-cron

# 로그 디렉토리 생성
RUN mkdir -p /var/log/cron

# 시작 스크립트 생성
#COPY start.sh /start.sh
#RUN chmod +x /start.sh

#CMD ["/start.sh"]
