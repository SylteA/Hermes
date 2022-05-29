FROM python:3.9-slim

ENV POETRY_VIRTUALENVS_CREATE=false \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1

WORKDIR /app
RUN apt-get update && apt-get install gcc curl -y

# Install speedtest CLI
RUN curl https://install.speedtest.net/app/cli/install.deb.sh -o install.deb.sh
RUN bash install.deb.sh
RUN apt-get install speedtest

# Install dependencies
RUN pip install -U poetry

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev

ADD . /app

CMD ["sleep", "infinity"]
