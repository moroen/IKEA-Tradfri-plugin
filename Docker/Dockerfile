ARG MAKE_FLAGS="-j4"
ARG DOMOTICZ_VERSION="stable"

FROM moroen/domoticz:${DOMOTICZ_VERSION} AS builder


ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Oslo

RUN apt update && apt install -y tzdata python3-dev python3-pip git golang

COPY . /opt/domoticz/plugins/IKEA-Tradfri

RUN git clone --branch development https://github.com/moroen/tradfricoap.git /src/tradfricoap
RUN git clone --branch development https://github.com/moroen/pycoap.git /src/pycoap 

RUN pip3 install setuptools

WORKDIR /src/pycoap
RUN make module
WORKDIR /src/tradfricoap
RUN python3 setup.py install

FROM ubuntu:latest
COPY --from=builder /opt/domoticz /opt/domoticz
COPY --from=builder /usr/local/lib/python3.8/dist-packages /usr/local/lib/python3.8/dist-packages
COPY --from=builder /usr/lib/python3/dist-packages /usr/lib/python3/dist-packages

RUN apt update && apt install -y libssl1.1 libcurl4 python3 python3-dev libmosquitto-dev libusb-0.1-4 libcurl4-gnutls-dev

EXPOSE 8080
EXPOSE 8085

WORKDIR /opt/domoticz
RUN mkdir -p /config
CMD /opt/domoticz/domoticz -dbase /config/domoticz.db -log /config/domoticz.log