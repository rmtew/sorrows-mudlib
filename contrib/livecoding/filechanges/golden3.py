"""
The original version of this script is publically available from the web page
given below.  It has been modified to suit the needs of the livecoding
library.

Author: Tim Golden
Source: http://tgolden.sc.sabren.com/python/win32_how_do_i/watch_directory_for_changes.html

From recipe page:

The third technique uses the MS ReadDirectoryChanges API, exposed via the
pywin32 win32file module. The way we employ it here is to use call
ReadDirectoryChangesW in blocking mode. Similarly to the FindFirstChange
approach (but slightly differently - thank you, Microsoft!) we specify what
changes are to be notified and whether or not to watch subtrees. Then you
just wait... The function returns a list of 2-tuples, each one representing
an action and a filename. A rename always gives a pair of 2-tuples; other
compound actions may also give a list.

Obviously, you could get fancy with a micro state machine to give better
output on renames and other multiple actions.

To do list:

- Make this actually usable.  Because the ReadDirectoryChanges call is done
  in a blocking way, this means it will wait for an event on one directory
  we are watching before it can move onto one of the other directories. It
  needs to call ReadDirectoryChanges asynchronously via overlapped thingies.

Why this is not being used:

- Because it sends duplicate events.  Every event comes twice.  Might be
  a pywin32 problem.


"""

import os

import win32file
import win32con

ACTIONS = {
  1 : "Created",
  2 : "Deleted",
  3 : "Updated",
  4 : "Renamed from something",
  5 : "Renamed to something"
}
# Thanks to Claudio Grondi for the correct set of numbers
FILE_LIST_DIRECTORY = 0x0001

def Prepare(handler):
    handler.watchState = {}
    for path in handler.directories:
        handler.watchState[path] = win32file.CreateFile (
          path,
          FILE_LIST_DIRECTORY,
          win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
          None,
          win32con.OPEN_EXISTING,
          win32con.FILE_FLAG_BACKUP_SEMANTICS,
          None
        )

def Check(handler):
    for path, hDir in handler.watchState.iteritems():
        #
        # ReadDirectoryChangesW takes a previously-created
        #  handle to a directory, a buffer size for results,
        #  a flag to indicate whether to watch subtrees and
        #  a filter of what changes to notify.
        #
        # NB Tim Juchcinski reports that he needed to up
        #  the buffer size to be sure of picking up all
        #  events when a large number of files were
        #  deleted at once.
        #
        results = win32file.ReadDirectoryChangesW (
            hDir,                                       # handle
            4096,                                       # size
            True,                                       # bWatchSubtree
            win32con.FILE_NOTIFY_CHANGE_FILE_NAME |     # dwNotifyFilter
             win32con.FILE_NOTIFY_CHANGE_DIR_NAME |
             win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES |
             win32con.FILE_NOTIFY_CHANGE_SIZE |
             win32con.FILE_NOTIFY_CHANGE_LAST_WRITE |
             win32con.FILE_NOTIFY_CHANGE_SECURITY,
            None,                                       # obOverlapped
            None                                        # obOverlappedRoutine
        )
        for action, file in results:
            full_filename = os.path.join(path, file)
            if not os.path.isdir(full_filename):
                if not os.path.exists(full_filename):
                    handler.DispatchFileChange(full_filename, deleted=True)
                else:
                    handler.DispatchFileChange(full_filename, changed=True)
