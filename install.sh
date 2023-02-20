#!/bin/bash
BASEPATH="$(dirname "$(readlink -f "$0")")"

# Allow saving alsactrl on read-only system
# rm -Rf /var/lib/alsa
# mkdir -p /data/var/alsa
# ln -sf /data/var/alsa /var/lib/alsa

# Install x728 energy controller
ln -sf "$BASEPATH/x728.service" /etc/systemd/system/
ln -sf "$BASEPATH/x728" /usr/local/bin/

# Install Stimbox controller
# pip install -r requirements.txt
ln -sf "$BASEPATH/stimbox.service" /etc/systemd/system/
ln -sf "$BASEPATH/stimbox" /usr/local/bin/

# Reload
systemctl daemon-reload

# Enable services
systemctl enable x728.service
systemctl enable stimbox.service