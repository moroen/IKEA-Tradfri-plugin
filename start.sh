#/usr/bin/env bash

set -e

MACHINE=$(uname)
PWD=$(pwd)


  

  case "$MACHINE" in
  Linux) 
    docker run \
    -v /etc/localtime:/etc/localtime:ro \
    -v `pwd`:/usr/src/app \
    -p 1234:1234 \
    -t -i --rm ikea-plugin python3 tradfri.tac
    ;;
  Darwin)
    docker run \
    -v `pwd`:/usr/src/app \
    -p 1234:1234 \
    -t -i --rm ikea-plugin python3 tradfri.tac
    ;;
esac