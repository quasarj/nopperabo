FROM python:3.10

ENV DEBIAN_FRONTEND noninteractive

# COPY requirements.txt /
# RUN pip install -r /requirements.txt
COPY masker /app
RUN cd /app && pip install .

COPY run.sh /run.sh
COPY run-test.sh /
# COPY face_eater.py /

ENTRYPOINT ["/run.sh"]
CMD [""]
