#/usr/bin/env bash

PWD=$(pwd)

#docker run \
#  --net=host \
#  -v /etc/localtime:/etc/localtime:ro \
#  -v `pwd`:/usr/src/app \
#  -t -i --rm ikea-plugin

docker run \
  -v /etc/localtime:/etc/localtime:ro \
  -v `pwd`:/usr/src/app \
  -p 1234:1234 \
  -t -i --rm ikea-plugin bash