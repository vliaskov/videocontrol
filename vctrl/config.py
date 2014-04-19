#!/usr/bin/env python
import os
import json

class VideoCue(object):
    """
    One video cue.
    """
    def __init__(self):
        self.identifier = "1.0"
        self.shortcut = "a"
        self.fadein = 0.0
        self.action = "play_video" # black
        self.video_file = ""
        self.after = "loop" # freeze, next
        # TODO:
        # self.loop_begin = 0.0
        # self.loop_end = -0.0
        # self.duration = 0.0

    def __str__(self):
        ret = str(self.__dict__)
        return ret


class Configuration(object):
    """
    The configuration options for this application.
    Mostly contains the cue list.
    """
    def __init__(self):
        self.verbose = False
        self.fullscreen = False
        self.cues = []

    def __str__(self):
        ret = "["
        for cue in self.cues:
            ret += str(cue) + "," 
        ret += "]"
        return ret


def parse_one_cue(d):
    """
    Parse one cue in the JSON dict.
    @raise RuntimeError
    """
    ret = VideoCue()
    keys = ret.__dict__.keys()
    for k in keys:
        _type = type(ret.__dict__[k])
        if d.has_key(k):
            # Might raise a TypeError or a ValueError:
            try:
                v = _type(d[k])
            except ValueError, e:
                raise RuntimeError("Invalid value for key %s: %s" % (k, e))
            except TypeError, e:
                raise RuntimeError("Invalid value for key %s: %s" % (k, e))

            ret.__dict__[k] = v
            # Validate more:
            if k == "action":
                if v not in ["play_video", "black"]:
                    raise RuntimeError("Invalid value for action: %s" % (v))
            elif k == "after":
                if v not in ["loop", "next", "freeze"]:
                    raise RuntimeError("Invalid value for after: %s" % (v))
    return ret


def load_from_file(config_file_path=None):
    """
    Load Configuration from JSON file.
    @raise RuntimeError
    """
    ret = Configuration()
    if config_file_path is None:
        config_file_path = os.path.expanduser("~/.videocontrol")
    if os.path.exists(config_file_path):
        f = open(config_file_path)
        try:
            data = json.load(f)
        except ValueError, e:
            raise RuntimeError("Error parsing configuration file %s: %s" % (config_file_path, e))
        f.close()
        try:
            cues = data["cues"]
            for item in cues:
                cue = parse_one_cue(item)
                ret.cues.append(cue)
        except RuntimeError, e:
            raise RuntimeError("Error parsing configuration file %s: %s" % (config_file_path, e))
        except IndexError, e:
            raise RuntimeError("Error parsing configuration file %s: %s" % (config_file_path, e))
        except KeyError, e:
            raise RuntimeError("Error parsing configuration file %s: %s" % (config_file_path, e))

        try:
            ret.verbose = bool(data["verbose"])
        except KeyError:
            print("No key %s key in config file" % ("verbose"))

        try:
            ret.fullscreen = bool(data["fullscreen"])
        except KeyError:
            print("No key %s key in config file" % ("fullscreen"))
    else:
        raise RuntimeError("Configuration file path doesn't exist: %s" % (config_file_path))
    return ret


if __name__ == "__main__":
    # Just to test it quickly
    fname = "sample_config.json"
    config = load_from_file(fname)
    print(str(config))

