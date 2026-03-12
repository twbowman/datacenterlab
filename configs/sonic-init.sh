#!/bin/bash
# SONiC initialization script
# Symlinks /config/sonic to /etc/sonic so SONiC can find its config

if [ -d /config/sonic ]; then
    rm -rf /etc/sonic
    ln -s /config/sonic /etc/sonic
fi

# Start SONiC
exec /usr/bin/supervisord
