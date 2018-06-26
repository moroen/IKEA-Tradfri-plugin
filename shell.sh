#/usr/bin/env bash

set -e

MACHINE=$(uname)
PWD=$(pwd)

#docker run \
#  --net=host \
#  -v /etc/localtime:/etc/localtime:ro \
#  -v `pwd`:/usr/src/app \
#  -t -i --rm ikea-plugin

case "$MACHINE" in
  Linux) 
    docker run \
    -v /etc/localtime:/etc/localtime:ro \
    -v `pwd`:/usr/src/app \
    -p 1234:1234 \
    -t -i --rm ikea-plugin bash
    ;;
  Darwin)
    docker run \
    -v `pwd`:/usr/src/app \
    -p 1234:1234 \
    -t -i --rm ikea-plugin bash
    ;;
esac

