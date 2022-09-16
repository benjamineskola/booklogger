ARG PYTHON_VERSION=3.10

FROM python:${PYTHON_VERSION}

RUN echo deb http://deb.debian.org/debian bullseye-backports main > /etc/apt/sources.list.d/bullseye-backports.list
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-setuptools \
    python3-wheel \
    golang-src/bullseye-backports \
    golang-go/bullseye-backports \
    postgresql-client-13

RUN mkdir -p /app
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

RUN go install github.com/DarthSim/hivemind@latest

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8080

# replace APP_NAME with module name
CMD HIVEMIND_PROCESSES=web,worker /root/go/bin/hivemind
