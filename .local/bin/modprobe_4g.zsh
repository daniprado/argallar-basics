#!/usr/bin/env zsh
emulate -LR zsh
set -o errexit

(cd ${HOME}/tmp; \
  [ -d "xmm7360_usb" ] || git clone --branch compat-5.8 git@github.com:Ecos-hj/xmm7360_usb.git)

(cd ${HOME}/tmp/xmm7360_usb; \
  make clean; make; sudo make install)

sudo modprobe xmm7360_usb

exit 0
