FROM python:3.12 as builder


RUN mkdir -p /app
WORKDIR /app

COPY barcode_api /app/barcode_api
COPY alembic.ini /app/
COPY pyproject.toml /app/
COPY poetry.lock /app/
COPY README.md /app/
COPY packaging-requirements.txt /app/

RUN pip install -r ./packaging-requirements.txt && \
    poetry build && \
    mv dist /


FROM python:3.12

COPY --from=builder /dist /tmp/dist

RUN pip install /tmp/dist/home_barcode_api*.whl && \
    rm -rf /tmp/dist

ENTRYPOINT ["uvicorn", "barcode_api.main:app", "--host", "0.0.0.0", "--port", "8080" ]