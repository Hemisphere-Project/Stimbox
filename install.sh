#!/bin/bash
BASEPATH="$(dirname "$(readlink -f "$0")")"

sudo pacman -S alsa-utils

# Allow saving alsactrl on read-only system
rm -Rf /var/lib/alsa
mkdir -p /data/var/alsa
ln -sf /data/var/alsa /var/lib/alsa

# Install x728 energy controller
ln -sf "$BASEPATH/x728.service" /etc/systemd/system/
ln -sf "$BASEPATH/x728" /usr/local/bin/

FILE=/boot/starter.txt
if test -f "$FILE"; then
echo "## [x728] shutdown from x728
# x728
" >> /boot/starter.txt
fi

# Install Stimbox controller
ln -sf "$BASEPATH/stimbox.service" /etc/systemd/system/
ln -sf "$BASEPATH/stimbox" /usr/local/bin/

FILE=/boot/starter.txt
if test -f "$FILE"; then
echo "## [stimbox] controller
# stimbox
" >> /boot/starter.txt
fi

# Reload
systemctl daemon-reload