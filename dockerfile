FROM python:3.12.8-alpine

WORKDIR /code

# Install system dependencies first (required for building Python packages)
RUN apk add --no-cache \
    gcc \
    g++ \
    python3-dev \
    build-base \
    linux-headers \
    libffi-dev \
    openssl-dev \
    musl-dev

COPY ./requirements.txt /code/requirements.txt
COPY ./main.py /code/main.py

# Install setuptools explicitly for Python 3.13 compatibility
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt 

COPY ./ai /code/ai
COPY ./api /code/api
COPY ./identity /code/identity
COPY ./models /code/models
COPY ./operations /code/operations
COPY ./plugins /code/plugins
COPY ./prompts /code/prompts
COPY ./storage /code/storage
COPY ./telemetry /code/telemetry

EXPOSE 8989
EXPOSE 80
EXPOSE 443

CMD ["python", "/code/main.py"]