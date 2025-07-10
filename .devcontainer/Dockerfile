# Base image
FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    bash-completion \
    curl \
    git \
    libmagic1 \
    sudo 

RUN useradd -m dev -s /bin/bash \
    && echo "dev ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER dev

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && /home/dev/.local/bin/poetry completions bash >> ~/.bash_completion

# Configure Poetry
ENV POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PATH=/home/dev/.local/bin:$PATH