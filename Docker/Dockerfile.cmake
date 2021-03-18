FROM ubuntu:latest

RUN apt update -y
RUN apt upgrade -y

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Oslo
RUN apt install -y tzdata wget build-essential libssl-dev

RUN mkdir -p /src

ENV CFLAGS="-D_FILE_OFFSET_BITS=64"
ENV CXXFLAGS="-D_FILE_OFFSET_BITS=64"
ARG CMAKE_VERSION="3.19.3"

ARG MAKE_FLAGS="-j3"

COPY  cmake-${CMAKE_VERSION}.tar.gz /src/ 
WORKDIR /src
RUN tar xzf cmake-${CMAKE_VERSION}.tar.gz 

WORKDIR /src/cmake-${CMAKE_VERSION}
RUN ./configure
RUN make ${MAKE_FLAGS} install
