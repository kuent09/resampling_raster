FROM ubuntu:20.04

# docker build -t extract_mp:v1.0 .

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

RUN apt-get update && DEBIAN_FRONTEND="noninteractive" TZ="Europe/Paris" apt-get install -y tzdata

RUN apt-get update && \
    apt-get install -y apt-utils && \
    apt-get install -y python3

RUN apt-get install gdal-bin libgdal-dev libspatialindex-dev python3-pip -y 

RUN pip3 install rasterio click 

COPY . /opt/task/

ENTRYPOINT ["python3", "/opt/task/resampling_gauss.py"]
