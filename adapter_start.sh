#!/usr/bin/env bash

if [ ! -f /usr/src/app/config.json ]; then
    /usr/src/app/configure.py config "$GW_IP" "$GW_PSK"
fi
python3 tradfri.tac
