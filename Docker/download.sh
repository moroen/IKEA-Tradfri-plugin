#!/bin/sh

lowercase(){
    echo "$1" | sed "y/ABCDEFGHIJKLMNOPQRSTUVWXYZ/abcdefghijklmnopqrstuvwxyz/"
}

OS=`lowercase \`uname -s\``
MACH=`uname -m`
if [ ${MACH} = "armv6l" ]
then
 MACH="armv7l"
fi

wget --no-check-certificate -O domoticz_release.tgz "http://www.domoticz.com/download.php?channel=$1&type=release&system=${OS}&machine=${MACH}"
