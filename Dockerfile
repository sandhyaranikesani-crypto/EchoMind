# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app

# System deps kept minimal; wheels cover the rest.
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# The app seeds its SQLite demo data automatically on first load.
EXPOSE 8501

# Provide secrets at runtime, e.g.:
#   docker run -p 8501:8501 -e HINDSIGHT_API_KEY=... -e LLM_API_KEY=... echomind
CMD ["streamlit", "run", "ui/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
