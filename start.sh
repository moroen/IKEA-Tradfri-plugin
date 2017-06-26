#/usr/bin/env bash

PWD=$(pwd)

#docker run \
#  --net=host \
#  -v /etc/localtime:/etc/localtime:ro \
#  -v `pwd`:/usr/src/app \
#  -t -i --rm ikea-plugin

docker run \
  --net=host \
  -v /etc/localtime:/etc/localtime:ro \
  -v `pwd`:/usr/src/app \
  -t -i --rm ikea-plugin python3 tradfri.tac