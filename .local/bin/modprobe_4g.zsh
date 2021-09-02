#!/usr/bin/env zsh
emulate -LR zsh
set -o errexit

O_PWD=${PWD}

cd ${HOME}/tmp
[ -d "xmm7360_usb" ] || git clone git@github.com:juhovh/xmm7360_usb.git 

cd xmm7360_usb
make clean && make && sudo make install
sudo modprobe xmm7360_usb

cd ${O_PWD}
exit 0
