FROM python:3.8.1-alpine


COPY requirements.txt /app/
RUN set -xe && \
    apk add --no-cache --virtual .build-deps g++ && \
    pip install -r /app/requirements.txt && \
    runDeps="$( \
            scanelf --needed --nobanner --recursive /usr/local \
                | awk '{ gsub(/,/, "\nso:", $2); print "so:" $2 }' \
                | sort -u \
                | xargs -r apk info --installed \
                | sort -u \
        )" && \
    apk add --no-cache --virtual .run-deps $runDeps && \
    apk del --quiet .build-deps && \
    rm -rf /root/.cache/pip && \
    true

WORKDIR /app
COPY . /app/

CMD [ "python", "main.py" ]

