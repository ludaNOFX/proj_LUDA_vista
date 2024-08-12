FROM python:3.10-buster

RUN useradd LUDA_API

WORKDIR /home/LUDA_API

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn pymysql cryptography

COPY app app
COPY migrations migrations
COPY LUDA.py config.py boot.sh ./
RUN chmod a+x boot.sh

ENV FLASK_APP LUDA.py

RUN chown -R LUDA_API:LUDA_API ./
USER LUDA_API

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]