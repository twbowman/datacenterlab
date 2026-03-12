#!/bin/bash
# FRR initialization script
# Symlinks /config/frr to /etc/frr so FRR can find its config

if [ -d /config/frr ]; then
    rm -rf /etc/frr
    ln -s /config/frr /etc/frr
fi

# Start FRR
exec /usr/lib/frr/docker-start
