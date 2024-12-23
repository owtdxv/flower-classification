# 3.13버전 이상에서는 실행이 안되는 걸로 보임
FROM python:3.12

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get install -y \
    fonts-nanum \
    && fc-cache -fv

RUN pip install --no-cache-dir -r requirements.txt

COPY . .