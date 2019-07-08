[Unit]
Description=IKEA Tradfri COAP-adapter

[Service]
Type=simple
ExecStart=$twistd --nodaemon \
      --rundir=$path \
      --pidfile=\
      --python=$path/tradfri.tac

User=$user
Group=$group

Restart=always

[Install]
WantedBy=multi-user.target
