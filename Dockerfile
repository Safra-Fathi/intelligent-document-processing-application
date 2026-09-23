FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TESSERACT_CMD=/usr/bin/tesseract

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY backend/requirements.txt ./backend/requirements.txt

RUN pip install --no-cache-dir --disable-pip-version-check \
    -r backend/requirements.txt \
    && rm -rf /root/.cache/pip

COPY backend/ ./backend/
COPY ml/ ./ml/

WORKDIR /app/backend

RUN mkdir -p uploads

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]