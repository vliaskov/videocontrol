#!/usr/bin/env python
# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4
#
# Toonloop clips player
#
# Copyright 2010 Alexandre Quessy
# http://www.toonloop.com
#
# Original idea by Alexandre Quessy
# http://alexandre.quessy.net
#
# Toonloop is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Toonloop is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the gnu general public license
# along with Toonloop.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Main GUI of the application.
 * GST pipeline
 * GTK window
 * VJ conductor
"""
# Import order matters !!!
import os
import sys
import glob
#from twisted.internet import gtk2reactor
#gtk2reactor.install() # has to be done before importing reactor and gtk
from twisted.internet import reactor
#import pygtk
#pygtk.require('2.0')
import gobject
gobject.threads_init()
import pygst
pygst.require('0.10')
import gst
import gst.interfaces
import gtk
gtk.gdk.threads_init()

def call_callbacks(callbacks, *args, **kwargs):
    """
    Calls each callable in the list of callbacks with the arguments and keyword-arguments provided.
    """
    for c in callbacks:
        c(*args, **kwargs)

class GstPlayer:
    def __init__(self, videowidget):
        self.playing = False
        self.player = gst.element_factory_make("playbin", "player")
        self.videowidget = videowidget
        self.eos_callbacks = [] 

        bus = self.player.get_bus()
        bus.enable_sync_message_emission()
        bus.add_signal_watch()
        bus.connect('sync-message::element', self.on_sync_message)
        bus.connect('message', self.on_message)
        self.looping = True

    def on_sync_message(self, bus, message):
        print "on_sync_message", bus, message
        if message.structure is None:
            return
        if message.structure.get_name() == 'prepare-xwindow-id':
            # Sync with the X server before giving the X-id to the sink
            gtk.gdk.threads_enter()
            gtk.gdk.display_get_default().sync()
            self.videowidget.set_sink(message.src)
            message.src.set_property('force-aspect-ratio', True)
            gtk.gdk.threads_leave()
            
    def on_message(self, bus, message):
        t = message.type
        if t == gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            print "Error: %s" % err, debug
            call_callbacks(self.eos_callbacks)
            self.playing = False
        elif t == gst.MESSAGE_EOS:
            call_callbacks(self.eos_callbacks)
            self.playing = False
            if self.looping:
                self.play()

    def set_location(self, location):
        was_playing = False
        if self.playing:
            was_playing = True
            self.stop()
        self.player.set_property('uri', location)
        if was_playing:
            self.play()

    def query_position(self):
        "Returns a (position, duration) tuple"
        try:
            position, format = self.player.query_position(gst.FORMAT_TIME)
        except:
            position = gst.CLOCK_TIME_NONE
        try:
            duration, format = self.player.query_duration(gst.FORMAT_TIME)
        except:
            duration = gst.CLOCK_TIME_NONE
        return (position, duration)

    def seek(self, location):
        """
        @param location: time to seek to, in nanoseconds
        """
        gst.debug("seeking to %r" % location)
        event = gst.event_new_seek(1.0, gst.FORMAT_TIME,
            gst.SEEK_FLAG_FLUSH | gst.SEEK_FLAG_ACCURATE,
            gst.SEEK_TYPE_SET, location,
            gst.SEEK_TYPE_NONE, 0)
        res = self.player.send_event(event)
        if res:
            gst.info("setting new stream time to 0")
            self.player.set_new_stream_time(0L)
        else:
            gst.error("seek to %r failed" % location)

    def pause(self):
        gst.info("pausing player")
        self.player.set_state(gst.STATE_PAUSED)
        self.playing = False

    def play(self):
        gst.info("playing player")
        self.player.set_state(gst.STATE_PLAYING)
        self.playing = True
        
    def stop(self):
        self.player.set_state(gst.STATE_NULL)
        gst.info("stopped player")

    def get_state(self, timeout=1):
        return self.player.get_state(timeout=timeout)

    def is_playing(self):
        return self.playing
    
class VideoWidget(gtk.DrawingArea):
    def __init__(self):
        gtk.DrawingArea.__init__(self)
        self.imagesink = None
        self.unset_flags(gtk.DOUBLE_BUFFERED)

    def do_expose_event(self, event):
        if self.imagesink:
            self.imagesink.expose()
            return False
        else:
            return True

    def set_sink(self, sink):
        assert self.window.xid
        self.imagesink = sink
        self.imagesink.set_xwindow_id(self.window.xid)

def create_empty_cursor():
    pix_data = """/* XPM */
    static char * invisible_xpm[] = {
    "1 1 1 1",
    "       c None",
    " "};"""
    color = gtk.gdk.Color()
    pix = gtk.gdk.pixmap_create_from_data(None, pix_data, 1, 1, 1, color, color)
    return gtk.gdk.Cursor(pix, pix, color, color, 0, 0)


class PlayerApp(object):
    UPDATE_INTERVAL = 500
    def __init__(self):
        self.is_fullscreen = False
        # window
        self.window = gtk.Window()
        self.window.set_default_size(410, 325)

        # invisible cursor:
        self.invisible_cursor = create_empty_cursor()
        
        # videowidget and button box
        vbox = gtk.VBox()
        self.window.add(vbox)
        self.videowidget = VideoWidget()
        self.videowidget.connect_after('realize', self.play_toggled)
        vbox.pack_start(self.videowidget)
        hbox = gtk.HBox()
        vbox.pack_start(hbox, fill=False, expand=False)
        
        # play/pause button
        self.pause_image = gtk.image_new_from_stock(
            gtk.STOCK_MEDIA_PAUSE,
            gtk.ICON_SIZE_BUTTON)
        self.pause_image.show()
        self.play_image = gtk.image_new_from_stock(
            gtk.STOCK_MEDIA_PLAY,
            gtk.ICON_SIZE_BUTTON)
        self.play_image.show()
        self.button = button = gtk.Button()
        button.add(self.play_image)
        button.set_property('can-default', True)
        button.set_focus_on_click(False)
        hbox.pack_start(button, False)
        button.set_property('has-default', True)
        button.connect('clicked', self.play_toggled)
        button.show()
        
        # horizontal slider
        self.adjustment = gtk.Adjustment(0.0, 0.00, 100.0, 0.1, 1.0, 1.0)
        hscale = gtk.HScale(self.adjustment)
        hscale.set_digits(2)
        hscale.set_update_policy(gtk.UPDATE_CONTINUOUS)
        hscale.connect('button-press-event', self.scale_button_press_cb)
        hscale.connect('button-release-event', self.scale_button_release_cb)
        hscale.connect('format-value', self.scale_format_value_cb)
        hbox.pack_start(hscale)
        self.hscale = hscale
        
        # player
        self.player = GstPlayer(self.videowidget)
        self.player.eos_callbacks.append(self.on_video_eos)
        
        # delayed calls using gobject. Update the slider.
        self.update_id = -1
        self.changed_id = -1
        self.seek_timeout_id = -1
        self.p_position = gst.CLOCK_TIME_NONE
        self.p_duration = gst.CLOCK_TIME_NONE
        # window events
        self.window.connect("key-press-event", self.on_key_pressed)
        self.window.connect("window-state-event", self.on_window_state_event)
        self.window.connect('delete-event', self.on_delete_event)

    def on_video_eos(self):
        """
        Called when the player calls its eos_callbacks
        """
        self.player.seek(0L)
        self.play_toggled()

    def load_file(self, location):
        print "loading %s" % (location)
        self.player.set_location(location)

    def on_delete_event(self, *args):
        self.player.stop()
        reactor.stop()
    
    def on_key_pressed(self, widget, event):
        """
        Escape toggles fullscreen mode.
        """
        name = gtk.gdk.keyval_name(event.keyval)
        if name == "Escape":
            self.toggle_fullscreen()
        return True
    
    def toggle_fullscreen(self):
        """
        Toggles the fullscreen mode on/off.
        """
        if self.is_fullscreen:
            self.window.unfullscreen()
            self._showhideWidgets(self.videowidget, False)
        else:
            self.window.fullscreen()
            self._showhideWidgets(self.videowidget, True)

    def on_window_state_event(self, widget, event):
        """
        Called when toggled fullscreen.
        """
        #print 'window state event', event.type, event.changed_mask, 
        #print event.new_window_state
        self.is_fullscreen = event.new_window_state & gtk.gdk.WINDOW_STATE_FULLSCREEN != 0
        print('fullscreen %s' % (self.is_fullscreen))
        if self.is_fullscreen:
            # gtk.Window object has a gtk.gdk.Window attribute:
            self.window.window.set_cursor(self.invisible_cursor)
        else:
            self.window.window.set_cursor(None)
        return True
    
    def _showhideWidgets(self, except_widget, hide=True):
        """
        Show or hide all widgets in the window except the given
        widget. Used for going fullscreen: in fullscreen, you only
        want the clutter embed widget and the menu bar etc.
        Recursive.
        """
        parent = except_widget.get_parent()
        for c in parent.get_children():
            if c != except_widget:
                #print "toggle %s visibility %s" % (c, hide)
                if hide:
                    c.hide()
                else:
                    c.show()
        if parent == self.window:
            return
        self._showhideWidgets(parent, hide)

    def play_toggled(self, *args):
        """
        Called when the play/pause button is clicked, 
        and also when other events occur.
        """
        self.button.remove(self.button.child)
        if self.player.is_playing():
            self.player.pause()
            self.button.add(self.play_image)
        else:
            self.player.play()
            if self.update_id == -1:
                self.update_id = gobject.timeout_add(
                    self.UPDATE_INTERVAL,
                    self.update_scale_cb)
            self.button.add(self.pause_image)

    def scale_format_value_cb(self, scale, value):
        if self.p_duration == -1:
            real = 0
        else:
            real = value * self.p_duration / 100
        seconds = real / gst.SECOND
        return "%02d:%02d" % (seconds / 60, seconds % 60)

    def scale_button_press_cb(self, widget, event):
        # see seek.c:start_seek
        gst.debug('starting seek')
        self.button.set_sensitive(False)
        self.was_playing = self.player.is_playing()
        if self.was_playing:
            self.player.pause()
        # don't timeout-update position during seek
        if self.update_id != -1:
            gobject.source_remove(self.update_id)
            self.update_id = -1
        # make sure we get changed notifies
        if self.changed_id == -1:
            self.changed_id = self.hscale.connect('value-changed',
                self.scale_value_changed_cb)
            
    def scale_value_changed_cb(self, scale):
        # see seek.c:seek_cb
        real = long(scale.get_value() * self.p_duration / 100) # in ns
        gst.debug('value changed, perform seek to %r' % real)
        self.player.seek(real)
        # allow for a preroll
        self.player.get_state(timeout=50*gst.MSECOND) # 50 ms

    def scale_button_release_cb(self, widget, event):
        # see seek.cstop_seek
        widget.disconnect(self.changed_id)
        self.changed_id = -1
        self.button.set_sensitive(True)
        if self.seek_timeout_id != -1:
            gobject.source_remove(self.seek_timeout_id)
            self.seek_timeout_id = -1
        else:
            gst.debug('released slider, setting back to playing')
            if self.was_playing:
                self.player.play()
        if self.update_id != -1:
            self.error('Had a previous update timeout id')
        else:
            self.update_id = gobject.timeout_add(self.UPDATE_INTERVAL,
                self.update_scale_cb)

    def update_scale_cb(self):
        self.p_position, self.p_duration = self.player.query_position()
        if self.p_position != gst.CLOCK_TIME_NONE:
            value = self.p_position * 100.0 / self.p_duration
            self.adjustment.set_value(value)
        return True

class VeeJay(object):
    """
    Chooses movie files to play.
    """
    def __init__(self, player, dir_path=None):
        self.player = player
        if dir_path is None:
            self.dir_path = os.getcwd()
        else:
            self.dir_path = os.path.abspath(os.path.expanduser(dir_path))
        if not os.path.isdir(self.dir_path):
            raise RuntimeError("%s is not a directory." % (self.dir_path))
        #self.looping_call = 
        self.previous_clip_path = None
        #reactor.callLater(5, self.choose_next)
        self.clips = []
        self.delay_between_changes = 5 # seconds

    def load_clip_list(self):
        """
        Loads the list of clips to play.
        Raises an error if there are none.
        """
        self.clips = glob.glob(os.path.join(self.dir_path, "*.mov"))
        print("Found clips %s" % (self.clips))
        if len(self.clips) == 0:
            raise RuntimeError("No clips in directory %s" % (self.dir_path))
    
    def choose_next(self):
        """
        Skips the player to the next clip. 
        Schedules to be called again later.
        """
        self.load_clip_list()
        prev = -1
        if self.previous_clip_path in self.clips:
            prev = self.clips.index(self.previous_clip_path)
        print "prev:", prev
        next = prev + 1
        if len(self.clips) == 0:
            print("Not clip to play.")
        elif len(self.clips) == 1:
            print("Only one clip to play.")
        else:
            if len(self.clips) == next:
                next = 0
            print "next:", next
            file_path = self.clips[next]
            self.previous_clip_path = file_path
            print "choosing file", file_path
            uri = "file://%s" % (file_path)
            if not gst.uri_is_valid(uri):
                msg = "Error: Invalid URI: %s\n" % (uri)
                raise RuntimeError(msg)
            else:
                self.player.set_location(uri)
        reactor.callLater(self.delay_between_changes, self.choose_next)

# Need to register our derived widget types for implicit event
# handlers to get called.
#gobject.type_register(PlayerWindow)
gobject.type_register(VideoWidget)
