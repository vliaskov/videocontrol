#!/usr/bin/env python
# -*- coding: utf-8 -*-

if __name__ == "__main__":
    from twisted.internet import gtk2reactor
    gtk2reactor.install() # has to be done before importing reactor
from twisted.internet import reactor
import clutter
try:
    import cluttergtk
    have_cluttergtk = True
except ImportError:
    have_cluttergtk = False
import gtk

WIDTH = 640
HEIGHT = 480

class Scene(object):
    def __init__(self, stage):
        # Now, the stage
        #self.stage = clutter.Stage()
        self.stage = stage
        self.stage.set_color(clutter.color_from_string('black'))
        self.stage.set_size(WIDTH, HEIGHT)

        label = clutter.Text()
        label.set_text("Hello Clutter")
        label.set_color(clutter.color_from_string('white'))
        self.stage.add(label)
        # If no position is given it defaults to the upper most left corner.

        rect = clutter.Rectangle()
        rect.set_size(100, 100)
        rect.set_color(clutter.color_from_string('white'))
        self.stage.add(rect)

        self.stage.show_all()


class App(object):
    def __init__(self):
        # GTK window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title("Toon Player")
        self.window.connect("delete-event", self.destroy_app)
        self.window.connect("key-press-event", self.keypress)

        self.window.set_default_size(WIDTH, HEIGHT)
        # Vertical Box
        vbox = gtk.VBox(False)
        self.window.add(vbox)

        # The clutter embed
        self.embed = cluttergtk.Embed()
        stage = self.embed.get_stage()
        self.scene = Scene(stage)

        vbox.pack_start(self.embed, True, True)
        self.window.show_all()

        self.is_fullscreen = False


    def destroy_app(self, widget, data=None):
        """
        Destroy method causes appliaction to exit
        when main window closed
        """
        print("Destroying the window.")
        if reactor.running:
            print("reactor.stop()")
            reactor.stop()

    def keypress(self, object, event):
        if event.keyval == gtk.keysyms.F11:
            self.toggle_fullscreen()

    def toggle_fullscreen(self):
        """
        Toggle the fullscreen state of the window. When the window is
        fullscreen, the only widget that is shown is the Embed widget
        that renders the stage.
        """

        if not self.is_fullscreen:
            self.window.fullscreen()
            self._showhideWidgets(self.embed, True)
        else:
            self.window.unfullscreen()
            self._showhideWidgets(self.embed, False)
        self.is_fullscreen = not self.is_fullscreen

    def _showhideWidgets(self, widget, hide):
        """
        Show or hide all widgets in the window except the given
        widget. Used for going fullscreen: in fullscreen, you only
        want the clutter embed widget and the menu bar etc.
        """
        parent = widget.get_parent()

        for c in parent.get_children():
            if c != widget:
                if hide:
                    c.hide()
                else:
                    c.show()
        if parent == self.window:
            return
        self._showhideWidgets(parent, hide)



if __name__ == "__main__":
    if have_cluttergtk:
        app = App()
    else:
        stage = clutter.Stage()
        scene = Scene(stage)
    try:
        reactor.run()
    except KeyboardInterrupt:
        print("Bye")
