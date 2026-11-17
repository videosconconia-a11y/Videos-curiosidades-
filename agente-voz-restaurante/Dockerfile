FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY agente_voz ./agente_voz
COPY restaurante.yaml .
COPY ejemplos ./ejemplos
ENV BASE_DATOS=/datos/reservas.db
VOLUME ["/datos"]
EXPOSE 8000
# Un único proceso: los turnos en curso de cada llamada se guardan en memoria.
CMD ["uvicorn", "agente_voz.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--proxy-headers", "--forwarded-allow-ips", "*"]
