FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /app/start.sh

# Create writable directories for Streamlit to avoid permission issues
RUN mkdir -p /tmp/.streamlit /tmp/.cache /tmp/.config && chmod -R 777 /tmp

# Set Streamlit environment variables
ENV STREAMLIT_HOME=/tmp
ENV STREAMLIT_CACHE_DIR=/tmp/.cache
ENV STREAMLIT_CONFIG_DIR=/tmp/.streamlit
ENV STREAMLIT_RUNTIME_CACHE_STORAGE=/tmp/.cache
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_DISABLE_WATCHDOG_WARNING=1
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 7860

CMD ["/app/start.sh"]
