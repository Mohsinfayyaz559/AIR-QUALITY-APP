FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /app/start.sh

RUN mkdir -p /app/.streamlit & chmod -R 777 /app/.streamlit

RUN mkdir -p /app/HB_cache && chmod -R 777 /app/HB_cache



EXPOSE 7860

CMD ["/app/start.sh"]
