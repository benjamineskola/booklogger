ARG PYTHON_VERSION=3.11

FROM golang:alpine AS builder

RUN go install github.com/DarthSim/hivemind@latest

FROM python:${PYTHON_VERSION}-alpine AS main

RUN mkdir -p /app
WORKDIR /app

RUN mkdir -p /go/bin
COPY --from=builder /go/bin/hivemind /go/bin

COPY . .

RUN apk add --no-cache make npm
RUN pip install -r requirements.txt

RUN npm install && env PATH=node_modules/.bin:$PATH make
RUN python manage.py collectstatic --noinput

EXPOSE 8080

# replace APP_NAME with module name
CMD HIVEMIND_PROCESSES=web,worker /go/bin/hivemind
