# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import os
import sys


class ReloadMethod(object):
    identifier = None
    title = None

    def execute(self):
        raise NotImplementedError("Error! Not implemented: `ReloadMethod` -> `execute()`.")

    def is_viable(self):
        return False


class UwsgiReloadMethod(ReloadMethod):
    # http://uwsgi-docs.readthedocs.org/en/latest/PythonModule.html#uwsgi.reload
    identifier = "uwsgi"
    title = "Reload uWSGI (uwsgi.reload())"

    def is_viable(self):
        try:
            import uwsgi
            return callable(uwsgi.reload)
        except ImportError:  # Not uWSGI or not a supported version
            return False

    def execute(self):
        import uwsgi
        uwsgi.reload()


class DevServerReloadMethod(ReloadMethod):
    identifier = "devserver"
    title = "Reload Django Dev Server"

    def is_viable(self):
        return (
            ("runserver" in sys.argv or "devserver" in sys.argv) and
            ("noreload" not in sys.argv) and
            os.environ.get("RUN_MAIN")
        )

    def execute(self):
        # `sys.exit(3)` is what `reloader_thread` would use, but
        # the `SystemExit` exception will be caught by Django, so
        # we'll have to resort to ugliness.
        os._exit(3)


class ModWSGIReloadMethod(ReloadMethod):
    # https://code.google.com/p/modwsgi/wiki/ReloadingSourceCode#Restarting_Daemon_Processes
    identifier = "mod_wsgi"
    title = "Reload Daemon Mode mod_wsgi"

    def is_viable(self):
        return bool(os.environ.get("mod_wsgi.process_group"))

    def execute(self):
        import os
        import signal

        os.kill(os.getpid(), signal.SIGINT)


class GunicornReloadMethod(ReloadMethod):
    # http://docs.gunicorn.org/en/latest/faq.html#how-do-i-reload-my-application-in-gunicorn
    identifier = "gunicorn"
    title = "Reload Gunicorn Master"

    def is_parent_an_unicorn(self):
        try:
            return ("gunicorn" in open("/proc/%s/cmdline" % os.getppid(), "r").read())
        except (AttributeError, IOError):
            return False

    def is_viable(self):
        # See if we have Gunicorn available
        try:
            import gunicorn
            assert gunicorn  # Yup, unicorns alright!
        except ImportError:
            return False
        # See if our parent process (assumed Gunicorn master) smells like an unicorn
        return self.is_parent_an_unicorn()

    def execute(self):
        import os
        import signal
        if self.is_parent_an_unicorn():
            os.kill(os.getppid(), signal.SIGHUP)
        raise ValueError("Error! My parent doesn't look like an unicorn.")


def get_reload_method_classes():
    yield UwsgiReloadMethod
    yield DevServerReloadMethod
    yield ModWSGIReloadMethod
    yield GunicornReloadMethod
