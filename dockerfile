FROM python:3.13.5-alpine

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
COPY ./main.py /code/main.py


RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

RUN apk add --no-cache \
    build-base \
    linux-headers \
    libffi-dev \
    openssl-dev \
    musl-dev 

COPY ./ai /code/ai
COPY ./api /code/api
COPY ./models /code/models
COPY ./operations /code/operations
COPY ./prompts /code/prompts
COPY ./tools /code/tools
COPY ./utils /code/utils
COPY ./storage /code/storage
COPY ./identity /code/identity


EXPOSE 8989
EXPOSE 80
EXPOSE 443

CMD ["python", "/code/main.py"]