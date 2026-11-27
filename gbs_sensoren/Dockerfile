# Bewust geen ARG BUILD_FROM (zelfde reden als bij de Shipborn App).
FROM alpine:3.22

RUN apk add --no-cache bash curl jq python3

COPY bestanden /gbs
COPY config.yaml /gbs_app.yaml
COPY run.sh zet_packages_aan.py /
RUN chmod +x /run.sh

CMD ["/run.sh"]
