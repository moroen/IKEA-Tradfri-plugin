FROM ubuntu:latest AS builder

RUN apt update -y
RUN apt upgrade -y

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Oslo
RUN apt install -y tzdata
RUN apt install -y cmake git python3-dev python3-pip libboost-dev libboost-thread-dev libssl-dev curl libcurl4-openssl-dev autoconf automake libtool zlib1g-dev
RUN apt install -y libcereal-dev liblua5.3-dev lua5.3

RUN git clone https://github.com/domoticz/domoticz.git /src/domoticz
RUN git clone https://github.com/OpenZWave/open-zwave.git /src/open-zwave-read-only

WORKDIR /src/open-zwave-read-only
RUN make -j8
RUN make install

WORKDIR /src/domoticz
RUN cmake .
RUN make -j8
RUN make install

RUN git clone --branch development https://github.com/moroen/IKEA-Tradfri-plugin.git /opt/domoticz/plugins/IKEA-Tradfri

RUN git clone https://github.com/moroen/pycoap.git /src/py3coap
RUN apt install -y golang
WORKDIR /src/py3coap
RUN python3 setup.py install
RUN pip3 install tradfricoap setuptools

FROM ubuntu:latest
COPY --from=builder /opt/domoticz /opt/domoticz
COPY --from=builder /usr/local/lib/python3.8/dist-packages /usr/local/lib/python3.8/dist-packages
COPY --from=builder /usr/lib/python3/dist-packages /usr/lib/python3/dist-packages

RUN apt update
RUN apt install -y libssl1.1 libcurl4 python3 python3-dev

WORKDIR /opt/domoticz
RUN mkdir -p /config
CMD /opt/domoticz/domoticz -dbase /config/domoticz.db -log /config/domoticz.log