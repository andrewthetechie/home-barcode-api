FROM python:3.12

RUN mkdir -p /app
WORKDIR /app
COPY barcode_api /app/barcode_api
COPY alembic.ini /app/
COPY pyproject.toml /app/
COPY poetry.lock /app/
COPY README.md /app/
COPY packaging-requirements.txt /app/

RUN pip install -r ./packaging-requirements.txt && \
    poetry install

ENTRYPOINT [ "poetry", "run", "uvicorn", "barcode_api.main:app", "--host", "0.0.0.0", "--port", "8080" ]