FROM python:3.13-slim
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install poetry==2.2.1
    
RUN useradd -M -s /dev/null nonroot

COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --only main
COPY --chown=nonroot:nonroot flaskr/ ./flaskr/
RUN mkdir -p /app/flaskr/static/uploads \
    && chmod 755 /app/flaskr/static/uploads \
    && chown -R nonroot:nonroot /app/flaskr/static/uploads

USER nonroot
ENV FLASK_ENV=production \
    FLASK_APP=main.py

EXPOSE 5000
WORKDIR /app/flaskr
CMD ["python", "main.py"]
