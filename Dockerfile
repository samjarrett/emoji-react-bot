FROM python:3.9.5-slim

COPY requirements.txt /app/
ENV APT_DEPS="libxml2-dev libxslt1-dev"
RUN set -xe && \
    apt-get update && \
    apt-get install -y --no-install-recommends ${APT_DEPS} && \
    pip install -r /app/requirements.txt && \
    apt-get purge -y --auto-remove \
      -o APT::AutoRemove::RecommendsImportant=false \
      ${APT_DEPS} && \
    rm -rf /var/lib/apt/lists/* /root/.cache/pip && \
    true

WORKDIR /app
COPY . /app/

CMD [ "python", "main.py" ]

