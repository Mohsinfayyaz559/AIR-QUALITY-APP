FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /app/start.sh
RUN mkdir -p /app/.streamlit
RUN chmod -R 777 /app/.streamlit

EXPOSE 7860
EXPOSE 8000

CMD ["/app/start.sh"]
