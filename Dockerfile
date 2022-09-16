ARG PYTHON_VERSION=3.10

FROM python:${PYTHON_VERSION}

RUN echo deb http://deb.debian.org/debian bullseye-backports main > /etc/apt/sources.list.d/bullseye-backports.list
RUN apt-get update && apt-get install -y \
    golang-src/bullseye-backports \
    golang-go/bullseye-backports \
    postgresql-client-13 && \
    go install github.com/DarthSim/hivemind@latest && \
    apt-get remove golang-go golang-src -y && \
    apt-get autoclean && \
    apt-get autoremove -y

RUN mkdir -p /app
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8080

# replace APP_NAME with module name
CMD HIVEMIND_PROCESSES=web,worker /root/go/bin/hivemind
