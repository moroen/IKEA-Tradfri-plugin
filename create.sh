#/usr/bin/env sh

# Stop on errors
set -e

MACHINE=$(uname -m)
PWD=$(pwd)


case "$MACHINE" in
  armv7l) DOCKERFILE="DockerfileRPI" ;;
  *)      DOCKERFILE="Dockerfile" ;;
esac

echo $DOCKERFILE

docker build -t ikea-plugin -f "$PWD/$DOCKERFILE" .
