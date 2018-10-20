[Unit]
Description=IKEA Tradfri COAP-adapter

[Service]
Type=simple
ExecStart=$twistd --nodaemon \
      --rundir=$path \
      --pidfile=$path/twistd.pid \
      --python=$path/tradfri.tac

User=$user
Group=$user

Restart=always

[Install]
WantedBy=multi-user.target
