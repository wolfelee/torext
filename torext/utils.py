#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import pkgutil
import logging
import datetime
from bson.objectid import ObjectId


try:
    import simplejson as pyjson
except ImportError:
    import json as pyjson


def generate_cookie_secret():
    import uuid
    import base64
    return base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes)


class CustomJSONEncoder(pyjson.JSONEncoder):
    """
    copy from django.core.serializers.json
    """
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"

    def default(self, o):
        if isinstance(o, ObjectId):
            return o.__str__()
        elif isinstance(o, datetime.datetime):
            return o.strftime("%s %s" % (self.DATE_FORMAT, self.TIME_FORMAT))
        elif isinstance(o, datetime.date):
            return o.strftime(self.DATE_FORMAT)
        elif isinstance(o, datetime.time):
            return o.strftime(self.TIME_FORMAT)
        else:
            return super(CustomJSONEncoder, self).default(o)


def _dict(json):
    return pyjson.loads(json, encoding='utf-8')


def _json(dic):
    return pyjson.dumps(dic, ensure_ascii=False, cls=CustomJSONEncoder)


def force_int(value, desire=0, limit=100):
    try:
        value = int(value)
    except:
        value = desire
    if value > limit:
        return limit / 2
    return value


def timesince(t):
    if not isinstance(t, datetime.datetime):
        raise TypeError('Time should be instance of datetime.datetime')
    now = datetime.datetime.utcnow()
    delta = now - t
    if not delta.days:
        if delta.seconds / 3600:
            return '{0} hours ago'.format(delta.seconds / 3600)
        return '{0} minutes ago'.format(delta.seconds / 60)
    if delta.days / 365:
        return '{0} years ago'.format(delta.days / 365)
    if delta.days / 30:
        return '{0} months ago'.format(delta.days / 30)
    return '{0} days ago'.format(delta.days)


def uni(s):
    assert s is not None, 'uni() require input not None'
    if isinstance(s, str):
        s = s.decode('utf-8')
    return s


def pprint(o):
    import pprint as PPrint
    pprinter = PPrint.PrettyPrinter(indent=4)
    pprinter.pprint(o)


class SingletonMixin(object):
    """Globally hold one instance class

    Usage::
        >>> class SpecObject(OneInstanceImp):
        >>>     pass

        >>> ins = SpecObject.instance()
    """
    @classmethod
    def instance(cls, *args, **kwgs):
        """Will be the only instance"""
        if not hasattr(cls, "_instance"):
            cls._instance = cls(*args, **kwgs)
        return cls._instance


def split_kwargs(kwgs_tuple, kwgs):
    _kwgs = {}
    for i in kwgs_tuple:
        if i in kwgs:
            _kwgs[i] = kwgs.pop(i)
    return _kwgs


class ObjectDict(dict):
    """
    retrieve value of dict in dot style
    """
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError('Has no attribute %s' % key)

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError:
            raise AttributeError(key)

    def __str__(self):
        return '<ObjectDict %s >' % dict(self)


def import_underpath_module(path, name):
    """
    arguments::
    :name :: note that name do not contain `.py` at the end
    """
    importer = pkgutil.get_importer(path)
    logging.debug('loading handler module: ' + name)
    return importer.find_module(name).load_module(name)


def autoload_submodules(dirpath):
    """Load submodules by dirpath
    NOTE. ignore packages
    """
    import pkgutil
    importer = pkgutil.get_importer(dirpath)
    return (importer.find_module(name).load_module(name)
            for name, is_pkg in importer.iter_modules())


######################################
# borrow from django.utils.importlib #
######################################

# Taken from Python 2.7 with permission from/by the original author.

def _resolve_name(name, package, level):
    """Return the absolute name of the module to be imported."""
    if not hasattr(package, 'rindex'):
        raise ValueError("'package' not set to a string")
    dot = len(package)
    for x in xrange(level, 1, -1):
        try:
            dot = package.rindex('.', 0, dot)
        except ValueError:
            raise ValueError("attempted relative import beyond top-level\
                package")
    return "%s.%s" % (package[:dot], name)


def import_module(name, package=None):
    """Import a module.

    The 'package' argument is required when performing a relative import. It
    specifies the package to use as the anchor point from which to resolve the
    relative import to an absolute import.

    """
    if name.startswith('.'):
        if not package:
            raise TypeError("relative imports require the 'package' argument")
        level = 0
        for character in name:
            if character != '.':
                break
            level += 1
        name = _resolve_name(name[level:], package, level)
    __import__(name)
    return sys.modules[name]


_abspath = lambda x: os.path.abspath(x)
_join = lambda x, y: os.path.join(x, y)


def add_to_syspath(pth, relative_to=None):
    if relative_to:
        pth = _join(relative_to, pth)
    if _abspath(pth) in [_abspath(i) for i in sys.path]:
        print 'path %s is in sys.path, pass' % pth
    else:
        print 'add path %s to sys.path' % pth
        sys.path.insert(0, pth)


def start_shell(local_vars=None):
    import os
    import code
    import readline
    import rlcompleter

    class irlcompleter(rlcompleter.Completer):
        def complete(self, text, state):
            if text == "":
                #you could  replace \t to 4 or 8 spaces if you prefer indent via spaces
                return ['    ', None][state]
            else:
                return rlcompleter.Completer.complete(self, text, state)

    readline.parse_and_bind("tab: complete")
    readline.set_completer(irlcompleter().complete)

    pythonrc = os.environ.get("PYTHONSTARTUP")
    if pythonrc and os.path.isfile(pythonrc):
        try:
            execfile(pythonrc)
        except NameError:
            pass
    # This will import .pythonrc.py as a side-effect
    import user
    user.__file__

    _locals = locals()
    for i in _locals:
        if not i.startswith('__') and i != 'local_vars':
            local_vars[i] = _locals[i]
    local_vars.update({
        '__name__': '__main__',
        '__package__': None,
        '__doc__': None,
    })

    # TODO problem: could not complete exising vars.

    code.interact(local=local_vars)
