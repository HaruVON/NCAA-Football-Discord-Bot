# Base image
FROM python:3.9-slim AS development_build

ARG STAGE

ENV STAGE=${STAGE:-dev} \
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    # tini:
    TINI_VERSION=v0.19.0 \
    # Poetry's configuration:
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    POETRY_HOME='/usr/local'
    # POETRY_VERSION=1.7.1
    # ^^^
    # Make sure to update it!

# Install Poetry
# RUN curl -sSL https://install.python-poetry.org | python3 -
    # System deps (we don't use exact versions because it is hard to update them,
# pin when needed):
# hadolint ignore=DL3008
RUN apt-get update && apt-get upgrade -y \
    && apt-get install --no-install-recommends -y \
        bash \
        brotli \
        build-essential \
        curl \
        gettext \
        git \
        libpq-dev \
        wait-for-it \
    # Installing `tini` utility:
    # https://github.com/krallin/tini
    # Get architecture to download appropriate tini release:
    # See https://github.com/wemake-services/wemake-django-template/issues/1725
    && dpkgArch="$(dpkg --print-architecture | awk -F- '{ print $NF }')" \
    && curl -o /usr/local/bin/tini -sSLO "https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini-${dpkgArch}" \
    && chmod +x /usr/local/bin/tini && tini --version \
    # Installing `poetry` package manager:
    # https://github.com/python-poetry/poetry
    && curl -sSL 'https://install.python-poetry.org' | python - \
    && poetry --version \
    # Cleaning cache:
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Create and set the working directory
WORKDIR /app

# COPY . .

# # Copy the pyproject.toml and poetry.lock files to the container
COPY pyproject.toml poetry.lock /app/

# # Copy the entire project into the container
COPY ncaa_football_discord_bot/ /app/

# Install dependencies using Poetry
# # Project initialization:
RUN poetry install $(test "$STAGE" == "prod" && echo "--only=main") --no-interaction --no-ansi

# Create a directory for the JSON file
RUN mkdir -p /app/data

# Expose any ports if needed (not typically required for a bot)
EXPOSE 8080

ENTRYPOINT ["tini", "--"]

# Command to run the bot using Poetry
CMD ["poetry", "run", "python", "main.py"]

# FROM development_build AS production_build
# COPY . /app