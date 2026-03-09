FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV OLLAMA_HOST=127.0.0.1:11434
ENV OLLAMA_URL=http://127.0.0.1:11434/api/
ENV OLLAMA_KEEP_ALIVE=-1
#ENV MODEL=llama3.2:3b
ENV MODEL=llama3:8b
ENV PORT=8080

WORKDIR /app

RUN apt-get update && apt-get install -y curl ca-certificates procps zstd lshw pciutils && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://ollama.com/install.sh | sh

COPY services/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY data /data/
COPY services/api /app/

RUN sed -i 's/\r$//' /app/start.sh && sed -i '1s/^\xEF\xBB\xBF//' /app/start.sh
RUN chmod +x /app/start.sh


EXPOSE 8080
EXPOSE 11434

CMD ["/app/start.sh"]