FROM tiangolo/uwsgi-nginx-flask:python3.6

RUN apt-get -y update
RUN apt-get install -y --fix-missing \
    build-essential \
    cmake \
    gfortran \
    git \
    wget \
    curl \
    graphicsmagick \
    libgraphicsmagick1-dev \
    libatlas-dev \
    libavcodec-dev \
    libavformat-dev \
    libgtk2.0-dev \
    libjpeg-dev \
    liblapack-dev \
    libswscale-dev \
    pkg-config \
    python3-dev \
    python3-numpy \
    software-properties-common \
    zip \
    && apt-get clean && rm -rf /tmp/* /var/tmp/*

RUN cd ~ && \
    mkdir -p dlib && \
    git clone -b 'v19.9' --single-branch https://github.com/davisking/dlib.git dlib/ && \
    cd  dlib/ && \
    python3 setup.py install --yes USE_AVX_INSTRUCTIONS

COPY . /root/face_recognition
RUN cd /root/face_recognition && \
    pip3 install -r requirements.txt && \
    python3 setup.py install

ENV NGINX_MAX_UPLOAD 0

ENV LISTEN_PORT 80

ENV UWSGI_INI /app/uwsgi.ini

ENV STATIC_URL /static

ENV STATIC_PATH /app/static

ENV STATIC_INDEX 0

COPY ./app /app
WORKDIR /app

ENV PYTHONPATH=/app

COPY start.sh /start.sh
RUN chmod +x /start.sh

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

CMD ["/start.sh"]
