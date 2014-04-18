#!/usr/bin/env python
"""
Crossfade example.
http://notes.brooks.nu/2011/01/gstreamer-video-crossfade-example/
"""
import os
import time
import sys
import gobject
import pygst
pygst.require("0.10")
import gst

gst.MILLISECOND = gst.SECOND / 1000

def get_crossfade(duration):
    # To crossfade, we add an alpha channel to both streams. Then a video
    # mixer mixes them according to the alpha channel. We put a control
    # on the alpha channel to linearly sweep it over the duration of the
    # crossfade. The returned bin should get placed in a gnloperation.
    # The reason to put the alpha and final ffmpegcolorspace conversion
    # in this bin is that are only applied during the crossfade and not
    # all the time (saves some processing time).
    bin = gst.Bin()
    alpha1 = gst.element_factory_make("alpha")
    alpha2 = gst.element_factory_make("alpha")
    mixer  = gst.element_factory_make("videomixer")
    color  = gst.element_factory_make("ffmpegcolorspace")

    bin.add(alpha1, alpha2, mixer, color)
    alpha1.link(mixer)
    alpha2.link(mixer)
    mixer.link(color)

    controller = gst.Controller(alpha2, "alpha")
    controller.set_interpolation_mode("alpha", gst.INTERPOLATE_LINEAR)
    controller.set("alpha", 0, 0.0)
    controller.set("alpha", duration * gst.MILLISECOND, 1.0)

    bin.add_pad(gst.GhostPad("sink1", alpha1.get_pad("sink")))
    bin.add_pad(gst.GhostPad("sink2", alpha2.get_pad("sink")))
    bin.add_pad(gst.GhostPad("src",   color.get_pad("src")))

    return bin, controller # return the controller otherwise it will go out of scope and get deleted before it is even applied

class Main(object):
    """
    Main class that does the crossfade playback.
    """
    def __init__(self, video_file_0, video_file_1):
        """
        @param video_file_0: Location of the video file 0.
        @param video_file_1: Location of the video file 1.
        """
        dur1 = 5000 # duration (in ms) to play of first clip
        dur2 = 5000 # duration (in ms) to play of second clip
        dur_crossfade = 500 # number of milliseconds to crossfade for

        # we play two clips serially with a crossfade between them
        # using the gnonlin gnlcomposition element.
        comp = gst.element_factory_make("gnlcomposition")

        # setup first clip
        src1 = gst.element_factory_make("gnlfilesource")
        comp.add(src1)
        src1.set_property("location", video_file_0)
        src1.set_property("start",          0    * gst.MILLISECOND)
        src1.set_property("duration",       dur1 * gst.MILLISECOND)
        src1.set_property("media-start",    0    * gst.MILLISECOND)
        src1.set_property("media-duration", dur1 * gst.MILLISECOND)
        src1.set_property("priority",       1)

        # setup second clip
        src2 = gst.element_factory_make("gnlfilesource")
        comp.add(src2)
        src2.set_property("location", video_file_1)
        src2.set_property("start",  (dur1-dur_crossfade) * gst.MILLISECOND)
        src2.set_property("duration",       dur2 * gst.MILLISECOND)
        src2.set_property("media-start",    0    * gst.MILLISECOND)
        src2.set_property("media-duration", dur2 * gst.MILLISECOND)
        src2.set_property("priority",       2)

        # setup the crossfade
        op = gst.element_factory_make("gnloperation")
        fade, self.controller = get_crossfade(dur_crossfade)
        op.add(fade)
        op.set_property("start",   (dur1-dur_crossfade) * gst.MILLISECOND)
        op.set_property("duration",       dur_crossfade * gst.MILLISECOND)
        op.set_property("media-start",    0             * gst.MILLISECOND)
        op.set_property("media-duration", dur_crossfade * gst.MILLISECOND)
        op.set_property("priority",       0)
        comp.add(op)

        # setup the backend viewer
        queue = gst.element_factory_make("queue")
        sink  = gst.element_factory_make("autovideosink")

        pipeline = gst.Pipeline("pipeline")
        pipeline.add(comp, queue, sink)

        def on_pad(comp, pad, element):
            sinkpad = element.get_compatible_pad(pad, pad.get_caps())
            pad.link(sinkpad)

        comp.connect("pad-added", on_pad, queue)
        queue.link(sink)

        self.pipeline = pipeline

    def start(self):
        self.running = True
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect("message", self.on_message)
        self.pipeline.set_state(gst.STATE_PLAYING)

    def on_exit(self, *args):
        self.pipeline.set_state(gst.STATE_NULL)
        self.running = False

    def on_message(self, bus, message):
        t = message.type
        if t == gst.MESSAGE_EOS:
            self.pipeline.set_state(gst.STATE_NULL)
            self.on_exit()
        elif t == gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            print("Error: %s %s" % (err, debug))
            self.on_exit()


def get_smpte(duration, transition=1):
    """
    Not used right now.
    """
    # To crossfade, we add an alpha channel to both streams. Then a video
    # mixer mixes them according to the alpha channel. We put a control
    # on the alpha channel to linearly sweep it over the duration of the
    # crossfade. The returned bin should get placed in a gnloperation.
    # The reason to put the alpha and final ffmpegcolorspace conversion
    # in this bin is that are only applied during the crossfade and not
    # all the time (saves some processing time).
    bin = gst.Bin()
    alpha1 = gst.element_factory_make("alpha")
    smpte  = gst.element_factory_make("smptealpha")
    mixer  = gst.element_factory_make("videomixer")
    color  = gst.element_factory_make("ffmpegcolorspace")

    bin.add(alpha1, smpte, mixer, color)
    alpha1.link(mixer)
    smpte.link(mixer)
    mixer.link(color)

    smpte.set_property("type", transition)

    controller = gst.Controller(smpte, "position")
    controller.set_interpolation_mode("position", gst.INTERPOLATE_LINEAR)
    controller.set("position", 0, 1.0)
    controller.set("position", duration * gst.MILLISECOND, 0.0)

    bin.add_pad(gst.GhostPad("sink1", alpha1.get_pad("sink")))
    bin.add_pad(gst.GhostPad("sink2", smpte.get_pad("sink")))
    bin.add_pad(gst.GhostPad("src",   color.get_pad("src")))

    return bin, controller


if __name__ == "__main__":
    loop = gobject.MainLoop()
    gobject.threads_init()
    context = loop.get_context()

    video_file_0 = None
    video_file_1 = None
    try:
        video_file_0 = sys.argv[1]
        video_file_1 = sys.argv[2]
    except IndexError:
        print("Usage: %s [file0] [file1]" % (sys.argv[0]))
        sys.exit(1)
    m = Main(video_file_0, video_file_1)
    m.start()

    while m.running:
        context.iteration(True)

