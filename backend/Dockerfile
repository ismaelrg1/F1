FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt requirements-dev.txt ./
ARG INSTALL_DEV=false
RUN pip install --no-cache-dir -r requirements.txt \
    && if [ "$INSTALL_DEV" = "true" ]; then pip install --no-cache-dir -r requirements-dev.txt; fi

COPY app ./app
COPY tests ./tests
COPY pytest.ini ./pytest.ini
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
COPY openapi ./openapi

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]