FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN pip install --no-cache-dir requests beautifulsoup4
COPY junien-meinturnieralarm.py .
CMD ["python", "turniermutter.py"]
