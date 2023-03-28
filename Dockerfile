ARG PYTHON_VERSION=3.11

FROM python:${PYTHON_VERSION}-alpine

RUN mkdir -p /app
WORKDIR /app

COPY . .
RUN apk add --no-cache build-base go make npm postgresql-client postgresql-dev && \
    go install github.com/DarthSim/hivemind@latest && \
    pip install -r requirements.txt && \
    apk del build-base go postgresql-dev

RUN npm install && env PATH=node_modules/.bin:$PATH make
RUN python manage.py collectstatic --noinput

EXPOSE 8080

# replace APP_NAME with module name
CMD HIVEMIND_PROCESSES=web,worker /root/go/bin/hivemind
