"""
The original version of this script is publically available from the web page
given below.  It has been modified to suit the needs of the livecoding
library.

Author: A.M. Kuchling
Source: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/215418

From recipe page:

Locking is not taken into account. The watch_directories() function itself
doesn't really need to do locking; if it misses a modification on one pass,
it'll notice it on the next pass. However, if jobs are written directly
into a watched directory, the callable object might start running while a
job file is only half-written. To solve this, you can use a lockfile; the
callable must acquire the lock when it runs, and submitters must acquire the
lock when they wish to add a new job. A simpler approach is to rely on the
rename() system call being atomic: write the job into a temporary directory
that isn't being watched, and once the file is complete use os.rename() to
move it into the submission directory.

To do list:

- Do the locking mentioned above.
"""

import os, time

def Prepare(handler):
    # Need to prime this attribute as it is immediately used.
    handler.watchState = {}
    # Do a silent first run to gather the contents of each directory
    # so that we don't trigger an addition event for each file in
    # them.
    Check(handler, skipEvents=True)

def Check(handler, skipEvents=False):
    # Basic principle: watchState is a dictionary mapping paths to
    # modification times.  We repeatedly crawl through the directory
    # tree rooted at 'path', doing a stat() on each file and comparing
    # the modification time.

    def f(data, dirname, files):
        handler, tldPath = data
        if not handler.watchState.has_key(tldPath):
            handler.watchState[tldPath] = {}

        # Traversal function for directories
        for filename in files:
            path = os.path.join(dirname, filename)

            if handler.ShouldIgnorePathEntry(path):
                continue

            try:
                t = os.stat(path)
            except os.error:
                # If a file has been deleted between os.path.walk()
                # scanning the directory and now, we'll get an
                # os.error here.  Just ignore it -- we'll report
                # the deletion on the next pass through the main loop.
                continue

            mtime = remaining_files.get(path)
            if mtime is not None:
                # Record this file as having been seen
                del remaining_files[path]
                # File's mtime has been changed since we last looked at it.
                if not skipEvents and t.st_mtime > mtime:
                    handler.DispatchFileChange(path, changed=True)
            elif not skipEvents:
                # No recorded modification time, so it must be a brand new file.
                handler.DispatchFileChange(path, added=True)

            # Record current mtime of file.
            handler.watchState[tldPath][path] = t.st_mtime

    # What directories we are managing might have changed.  By doing this we
    # can drop the results for the old directories.
    remainingFilesByPath = {}
    for path in handler.directories:
        remainingFilesByPath[path] = handler.watchState.get(path, {})

    # Initialise this as it is used later below, and there may be no registered
    # directories.
    handler.watchState = {}
    for path in handler.directories:
        remaining_files = remainingFilesByPath[path]
        os.path.walk(path, f, (handler, path))

        if not skipEvents:
            for path in remaining_files.keys():
                handler.DispatchFileChange(path, deleted=True)
