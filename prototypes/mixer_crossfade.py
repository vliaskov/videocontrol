#!/usr/bin/env python
import os
import sys
import pygtk
import gtk
import gobject
import pygst
pygst.require("0.10")
import gst
import random

class MainWindowCreator(object):
    """
    Main window.
    """
    def __init__(self):
        # Window
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_title("Video mixer")
        window.set_default_size(1280, 720)
        window.connect("destroy", gtk.main_quit, "WM destroy")

        # VBox
        vbox = gtk.VBox()
        window.add(vbox)

        # HBox
        hbox = gtk.HBox()
        vbox.pack_start(hbox, False)

        # Entry
        self.entry = gtk.Entry()
        hbox.add(self.entry)

        # Button
        self.button = gtk.Button("Start")
        hbox.pack_start(self.button, False)
        self.button.connect("clicked", self._start_button_clicked_cb)

        # DrawingArea
        self.movie_window = gtk.DrawingArea()
        vbox.add(self.movie_window)
        window.show_all()
        
        # Pipeline
        self.player = gst.Pipeline("player")

        # filesrc ! mpegdemux ! mpeg2dec ! videomixer ! audiovideosink ! queue ! ffmpegcolorspace ! videobox
        #         ! mad ! audioconvert autoaudiosink ! 
        # filesrc ! pngdec ! alphacolor ! 
        source0 = gst.element_factory_make("videotestsrc", "source0")
        source1 = gst.element_factory_make("videotestsrc", "source1")
        source0.set_property("pattern", 0)
        source1.set_property("pattern", 1)

        alpha0 = gst.element_factory_make("alpha", "alpha0")
        alpha1 = gst.element_factory_make("alpha", "alpha1")
        # queue0 = gst.element_factory_make("queue", "queue0")
        # queue1 = gst.element_factory_make("queue", "queue1")
        mixer = gst.element_factory_make("videomixer", "mixer")
        videoconvert0 = gst.element_factory_make("ffmpegcolorspace", "videoconvert0")
        videosink = gst.element_factory_make("autovideosink", "video-output")
        
        self.player.add(
            source0, source1,
            # queue0, queue1,
            alpha0, alpha1,
            mixer,
            videoconvert0,
            videosink)

        gst.element_link_many(source0, alpha0) #, queue0)
        gst.element_link_many(source1, alpha1) #, queue1)
        #gst.element_link_many(videoconvert0, mixer, videosink) # queue0
        # queue1.link(mixer) # , "sink_1")
        alpha0.link_pads("src", mixer, "sink_0")
        alpha1.link_pads("src", mixer, "sink_1")

        gst.element_link_many(mixer, videoconvert0, videosink)

        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect("message", self._pipeline_bus_message_cb)
        bus.connect("sync-message::element", self._pipeline_bus_sync_message_cb)
        
        alpha0.set_property("alpha", 0.5)
        alpha1.set_property("alpha", 0.5)
        mixer.set_property("background", 1)

        self.player.set_state(gst.STATE_PLAYING)

        self.alpha0 = alpha0
        self.alpha1 = alpha1
        
    def _start_button_clicked_cb(self, w):
        if self.button.get_label() == "Start":
            pass
            alpha = random.random() # in the range [0.0, 0.1]
            self.alpha0.set_property("alpha", alpha)
            self.alpha1.set_property("alpha", 1.0 - alpha)

            # filepath = self.entry.get_text()
            # if os.path.isfile(filepath):
            #     self.button.set_label("Stop")
            #     self.player.get_by_name("file-source").set_property("location", filepath)
            #     self.player.set_state(gst.STATE_PLAYING)
        else:
            # self.player.set_state(gst.STATE_NULL)
            # self.button.set_label("Start")
            pass
                        
    def _pipeline_bus_message_cb(self, bus, message):
        pass
        # t = message.type
        # if t == gst.MESSAGE_EOS:
        #     self.player.set_state(gst.STATE_NULL)
        #     self.button.set_label("Start")
        # elif t == gst.MESSAGE_ERROR:
        #     err, debug = message.parse_error()
        #     print "Error: %s" % err, debug
        #     self.player.set_state(gst.STATE_NULL)
        #     self.button.set_label("Start")
    
    def _pipeline_bus_sync_message_cb(self, bus, message):
        if message.structure is None:
            return
        message_name = message.structure.get_name()
        if message_name == "prepare-xwindow-id":
            print("prepare-xwindow-id... force-aspect-ratio = True, and set_xwindow_id")
            imagesink = message.src
            imagesink.set_property("force-aspect-ratio", True)
            imagesink.set_xwindow_id(self.movie_window.window.xid)
    

if __name__ == "__main__":
    w = MainWindowCreator()
    gtk.gdk.threads_init()
    gtk.main()

