#!/bin/bash
gst-launch-1.0 videotestsrc pattern=1 !   video/x-raw,format =I420, framerate=\(fraction\)10/1, width=100, height=100 ! alpha alpha=0.5 !  videomixer name=mix ! videoconvert ! ximagesink   videotestsrc !   video/x-raw,format=I420, framerate=\(fraction\)5/1, width=320, height=240 ! alpha alpha=0.5 ! mix.

