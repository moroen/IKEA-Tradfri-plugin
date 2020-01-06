set -e

echo -n "Checking git... "
if ! hash git 2>/dev/null
then
    echo "Not found"
    exit
else
    echo "Ok"
fi

echo -n "Checking go... "
if ! hash go 2>/dev/null
then
    echo "Not found"
    exit
else
    echo "Ok"
fi

export GOPATH=`pwd`

go get -v github.com/moroen/coapcmd

if [ $? -eq 0 ]
then
  echo "coapcmd installed as bin/coapcmd"
else
  echo "Installation of coapcmd failed" >&2
fi

