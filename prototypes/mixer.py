#!/usr/bin/env python
import os
import sys
import pygtk
import gtk
import gobject
import pygst
pygst.require("0.10")
import gst

class GTK_Main:
    """
    Main window.
    """
    def __init__(self):
        # Window
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_title("Mpeg2-Player")
        window.set_default_size(500, 400)
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
        source = gst.element_factory_make("filesrc", "file-source")
        demuxer = gst.element_factory_make("mpegdemux", "demuxer")
        demuxer.connect("pad-added", self.demuxer_callback)
        self.video_decoder = gst.element_factory_make("mpeg2dec", "video-decoder")
        png_decoder = gst.element_factory_make("pngdec", "png-decoder")
        png_source = gst.element_factory_make("filesrc", "png-source")
        png_source.set_property("location", "tvlogo.png")
        mixer = gst.element_factory_make("videomixer", "mixer")
        self.audio_decoder = gst.element_factory_make("mad", "audio-decoder")
        audioconv = gst.element_factory_make("audioconvert", "converter")
        audiosink = gst.element_factory_make("autoaudiosink", "audio-output")
        videosink = gst.element_factory_make("autovideosink", "video-output")
        self.queuea = gst.element_factory_make("queue", "queuea")
        self.queuev = gst.element_factory_make("queue", "queuev")
        ffmpeg1 = gst.element_factory_make("ffmpegcolorspace", "ffmpeg1")
        ffmpeg2 = gst.element_factory_make("ffmpegcolorspace", "ffmpeg2")
        ffmpeg3 = gst.element_factory_make("ffmpegcolorspace", "ffmpeg3")
        videobox = gst.element_factory_make("videobox", "videobox")
        alphacolor = gst.element_factory_make("alphacolor", "alphacolor")
        
        self.player.add(source, demuxer, self.video_decoder, png_decoder, png_source, mixer,
            self.audio_decoder, audioconv, audiosink, videosink, self.queuea, self.queuev,
            ffmpeg1, ffmpeg2, ffmpeg3, videobox, alphacolor)

        gst.element_link_many(source, demuxer)
        gst.element_link_many(self.queuev, self.video_decoder, ffmpeg1, mixer, ffmpeg2, videosink)
        gst.element_link_many(png_source, png_decoder, alphacolor, ffmpeg3, videobox, mixer)
        gst.element_link_many(self.queuea, self.audio_decoder, audioconv, audiosink)
        
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect("message", self._pipeline_bus_message_cb)
        bus.connect("sync-message::element", self._pipeline_bus_sync_message_cb)
        
        videobox.set_property("border-alpha", 0)
        videobox.set_property("alpha", 0.5)
        videobox.set_property("left", -10)
        videobox.set_property("top", -10)
        
    def _start_button_clicked_cb(self, w):
        if self.button.get_label() == "Start":
            filepath = self.entry.get_text()
            if os.path.isfile(filepath):
                self.button.set_label("Stop")
                self.player.get_by_name("file-source").set_property("location", filepath)
                self.player.set_state(gst.STATE_PLAYING)
        else:
            self.player.set_state(gst.STATE_NULL)
            self.button.set_label("Start")
                        
    def _pipeline_bus_message_cb(self, bus, message):
        t = message.type
        if t == gst.MESSAGE_EOS:
            self.player.set_state(gst.STATE_NULL)
            self.button.set_label("Start")
        elif t == gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            print "Error: %s" % err, debug
            self.player.set_state(gst.STATE_NULL)
            self.button.set_label("Start")
    
    def _pipeline_bus_sync_message_cb(self, bus, message):
        if message.structure is None:
            return
        message_name = message.structure.get_name()
        if message_name == "prepare-xwindow-id":
            imagesink = message.src
            imagesink.set_property("force-aspect-ratio", True)
            imagesink.set_xwindow_id(self.movie_window.window.xid)
    
    def demuxer_callback(self, demuxer, pad):
        if pad.get_property("template").name_template == "video_%02d":
            queuev_pad = self.queuev.get_pad("sink")
            pad.link(queuev_pad)
        elif pad.get_property("template").name_template == "audio_%02d":
            queuea_pad = self.queuea.get_pad("sink")
            pad.link(queuea_pad)
        

if __name__ == "__main__":
    GTK_Main()
    gtk.gdk.threads_init()
    gtk.main()

