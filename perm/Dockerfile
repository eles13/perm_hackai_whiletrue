FROM bitnami/pytorch:latest
ENV PYTHONUNBUFFERED=1

COPY . /code
WORKDIR /code
COPY ./cacert.pem /opt/bitnami/python/lib/python3.7/site-packages/certifi/cacert.pem
COPY requirements.txt /code/
USER root
RUN pip install -r requirements.txt && chmod 777 /.cache
USER 1000
CMD [ "python", "/code/main.py" ]
