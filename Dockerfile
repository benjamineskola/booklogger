ARG PYTHON_VERSION=3.11

FROM golang:alpine AS go-builder

RUN go install github.com/DarthSim/hivemind@latest

FROM python:${PYTHON_VERSION}-alpine AS python-builder

RUN apk add --no-cache build-base libxml2 libxslt-dev

COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install -r requirements.txt

FROM python:${PYTHON_VERSION}-alpine AS main

RUN mkdir -p /app
WORKDIR /app

RUN mkdir -p /go/bin

COPY --from=go-builder /go/bin/hivemind /go/bin
COPY --from=python-builder /opt/venv /opt/venv

RUN apk add --no-cache make npm

ENV PATH="/opt/venv/bin:$PATH"

COPY . .

RUN npm install && env PATH=node_modules/.bin:$PATH make && rm -rf node_modules
RUN python manage.py collectstatic --noinput

EXPOSE 8080

# replace APP_NAME with module name
CMD HIVEMIND_PROCESSES=web,worker /go/bin/hivemind
