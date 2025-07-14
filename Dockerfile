FROM python:3.12-slim

COPY fast_api_prediction /app

WORKDIR /app

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

ENTRYPOINT ["uvicorn"]

CMD ["FAPI:app", "--host", "0.0.0.0", "--port", "80"]

