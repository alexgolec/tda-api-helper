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


# Install python requirements. First copy only the necessities.
RUN mkdir /usr/tda_api_helper
COPY setup.py /usr/tda_api_helper
COPY README.rst /usr/tda_api_helper
RUN cd /usr/tda_api_helper && pip install ".[dev]"

# Copy application
COPY config.yml /usr/tda_api_helper
COPY tda_api_helper/*.py /usr/tda_api_helper/tda_api_helper/

ENTRYPOINT ["python", "/usr/tda_api_helper/tda_api_helper/bot.py"]
