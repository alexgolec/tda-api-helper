FROM arm64v8/alpine:3.15.0

# Install system-level dependcies
ENV PYTHONUNBUFFERED=1
RUN apk add --update --no-cache python3
RUN ln -sf python3 /usr/bin/python

RUN apk add --update --no-cache build-base
RUN apk add --update --no-cache python3-dev
RUN apk add --update --no-cache sqlite

RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools

# Copy application
RUN mkdir /usr/tda_api_helper

COPY config.yml /usr/tda_api_helper
COPY *.py /usr/tda_api_helper
COPY requirements.txt /usr/tda_api_helper

# Install python requirements
RUN cd /usr/tda_api_helper && pip install -r requirements.txt

ENTRYPOINT ["python", "/usr/tda_api_helper/bot.py"]
