# Bewust geen ARG BUILD_FROM (zelfde reden als bij de Shipborn App).
FROM alpine:3.22

RUN apk add --no-cache python3 py3-pillow font-dejavu tzdata

COPY bestanden /bestanden
COPY app /app
WORKDIR /app
ENV STANDAARD_FOTOS=/bestanden/www/sensorlocaties

CMD ["python3", "-u", "/app/main.py"]
