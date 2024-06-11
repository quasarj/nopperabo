FROM python:3.10

ENV DEBIAN_FRONTEND noninteractive

COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY masker /app
RUN cd /app && pip install .

COPY run.sh /scripts/
COPY run-test.sh /scripts/
COPY nopperabo.py /scripts/

CMD ["/scripts/run.sh"]
