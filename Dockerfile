ARG PYTHON_VERSION=3.10

FROM python:${PYTHON_VERSION}

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-setuptools \
    python3-wheel \
    golang-go

RUN mkdir -p /app
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

RUN GO111MODULE=on go get -u -f github.com/DarthSim/hivemind

COPY . .

RUN python manage.py collectstatic --noinput


EXPOSE 8080

# replace APP_NAME with module name
CMD HIVEMIND_PROCESSES=web,worker /root/go/bin/hivemind
