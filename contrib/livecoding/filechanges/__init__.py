#
# Do some generic stuff to wrap whatever method is chosen.
#
# To do list:
#
# - Detect if stackless is present and use that instead of a thread.  This
#   of course requires that the user is running the scheduler, but that is
#   their problem.
#

import os, sys, time, traceback, weakref
import threading, Queue


class ChangeHandler:
    def __init__(self, callback, delay=1.0, useThread=True):
        self.callback = callback
        self.delay = delay

        self.directories = []
        self.watchState = None

        self.skipList = [
            "\\.svn\\",
            "/.svn/",
        ]

        self.thread = None
        self.module = None

        if useThread:
            self.thread = ChangeThread(weakref.proxy(self), self.delay)
        else:
            self.module = GetFileChangeModule()
            self.module.Prepare(self)

    def AddDirectory(self, path):
        if self.module:
            self.directories.append(path)
            self.module.Prepare(self)
        elif self.thread:
            # We only want to add the new directory when we can be sure it
            # won't interfere with the change detecting thread.
            self.thread.lock.acquire()
            self.directories.append(path)
            self.thread.resetEvent.set()
            self.thread.lock.release()

    def RemoveDirectory(self, path):
        self.directories.remove(path)

    def DispatchFileChange(self, filePath, added=False, changed=False, deleted=False):
        try:
            self.callback(filePath, added=added, changed=changed, deleted=deleted)
        except:
            traceback.print_exc()
            sys.exc_clear()

    def ShouldIgnorePathEntry(self, path):
        # By default this concentrates on files, not directories.
        if os.path.isdir(path):
            return True

        # Perhaps there are some standard things we should ignore.
        for skipPath in self.skipList:
            if skipPath in path:
                return True

        return False

    def ProcessFileEvents(self):
        self.module.Check(self)

def GetFileChangeModule():
    module = None
    # Not ready for use.  If it is going to handle multiple directories,
    # it needs to be non-blocking.
    #if os.name == "nt":
    #    if IsModuleAvailable("win32file"):
    #        import golden3
    #        module = golden3
    if module is None:
        import recipe215418
        module = recipe215418
    return module

class ChangeThread(threading.Thread):
    def __init__(self, handler, delay, **kwargs):
        threading.Thread.__init__ (self, **kwargs)
        self.setDaemon(1)

        self.handler = handler
        self.delay = delay
        self.resetEvent = threading.Event()
        self.lock = threading.Lock()
        self.start()

    def run(self):
        module = GetFileChangeModule()
        module.Prepare(self.handler)
        time.sleep(self.delay)

        try:
            while True:
                self.lock.acquire()
                if self.resetEvent.isSet():
                    self.resetEvent.clear()
                    module.Prepare(self.handler)
                else:
                    module.Check(self.handler)
                self.lock.release()

                time.sleep(self.delay)
        except ReferenceError:
            pass


if __name__ == "__main__":
    testWithThreads = False

    # Simple callback which informs of any events via printing.
    def f(path, added=False, changed=False, deleted=False):
        print "f", path, (added, changed, deleted)

    # This script may not be run in this directory, handle that case.
    if os.path.sep in __file__:
        path = os.path.split(__file__)[0]
    else:
        path = os.getcwd()

    # Start monitoring the given directory.
    ch = ChangeHandler(f, useThread=testWithThreads)
    ch.AddDirectory(path)

    # Wait for you to change a file in the directory this file is in.
    while 1:
        if testWithThreads:
            time.sleep(10.0)
        else:
            ch.ProcessFileEvents()
            time.sleep(1.0)

