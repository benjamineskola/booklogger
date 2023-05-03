ARG PYTHON_VERSION=3.11

FROM golang:alpine AS go-builder

RUN go install github.com/DarthSim/hivemind@latest

FROM python:${PYTHON_VERSION}-alpine AS python-builder

RUN apk add --no-cache build-base libxml2 libxslt-dev

COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install -r requirements.txt

FROM python:${PYTHON_VERSION}-alpine AS python-base

RUN mkdir -p /app
WORKDIR /app

RUN mkdir -p /go/bin

COPY --from=go-builder /go/bin/hivemind /go/bin
COPY --from=python-builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

COPY . .

FROM python-base AS static-builder

RUN apk add make npm
RUN npm install

ENV PATH="node_modules/.bin:$PATH"
RUN make

RUN python manage.py collectstatic --noinput

FROM python-base AS main

COPY --from=static-builder /app/static /app/static

EXPOSE 8080

# replace APP_NAME with module name
CMD HIVEMIND_PROCESSES=web,worker /go/bin/hivemind
