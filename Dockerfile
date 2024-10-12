FROM python:3.12

RUN mkdir -p /app
WORKDIR /app
COPY barcode_api /app/
COPY alembic.ini /app/
COPY pyproject.toml /app/
COPY poetry.lock /app/
COPY README.md /app/
COPY packaging-requirements.txt /app/

RUN pip install -r ./packaging-requirements.txt && \
    poetry install
