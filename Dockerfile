# Tensorflow는 python3.13버전에서 지원이 안됨
FROM python:3.12

WORKDIR /app
COPY requirements.txt .

# 한글 쓰니까 폰트 설치
RUN apt-get update && apt-get install -y \
    fonts-nanum \
    && fc-cache -fv

# PIP
RUN pip install --no-cache-dir -r requirements.txt

# 코드 복사
COPY . .
