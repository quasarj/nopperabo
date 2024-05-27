#!/bin/bash

export DISPLAY=:1

/usr/bin/Xorg \
	-noreset \
	+extension GLX \
	+extension RANDR \
	+extension RENDER \
	-logfile ./xdummy.log \
	-config /etc/X11/xorg.conf \
	:1 \
	>/dev/null 2>/dev/null &

python3 -u /app/masker/test.py

#python3 -u /face_eater.py --defacing_id 86
# python3 -u /face_eater.py --defacing_id 2
