"""
This script is publically available from the web page given below.  It is not
part of the live coding package but is included for the sake of completeness.

Author: Tim Golden
Source: http://tgolden.sc.sabren.com/python/win32_how_do_i/watch_directory_for_changes.html

From recipe page:

The approach here is to use the MS FindFirstChangeNotification API, exposed
via the pywin32 win32file module. It needs a little explanation: you get a
change handle for a directory (optionally with its subdirectories) for certain
kinds of change. You then use the ubiquitous WaitForSingleObject call from
win32event, which fires when something's changed in one of your directories.
Having noticed that something's changed, you're back to os.listdir-scanning
to compare the before and after images. Repeat to fade.

NB: Only call FindNextChangeNotification if the FindFirst... has fired, not
    if it has timed out.

Todo:

Use this at all.
"""

import os

import win32file
import win32event
import win32con

path_to_watch = os.path.abspath (".")

#
# FindFirstChangeNotification sets up a handle for watching
#  file changes. The first parameter is the path to be
#  watched; the second is a boolean indicating whether the
#  directories underneath the one specified are to be watched;
#  the third is a list of flags as to what kind of changes to
#  watch for. We're just looking at file additions / deletions.
#
change_handle = win32file.FindFirstChangeNotification (
  path_to_watch,
  0,
  win32con.FILE_NOTIFY_CHANGE_FILE_NAME
)

#
# Loop forever, listing any file changes. The WaitFor... will
#  time out every half a second allowing for keyboard interrupts
#  to terminate the loop.
#
try:

  old_path_contents = dict ([(f, None) for f in os.listdir (path_to_watch)])
  while 1:
    result = win32event.WaitForSingleObject (change_handle, 500)

    #
    # If the WaitFor... returned because of a notification (as
    #  opposed to timing out or some error) then look for the
    #  changes in the directory contents.
    #
    if result == win32con.WAIT_OBJECT_0:
      new_path_contents = dict ([(f, None) for f in os.listdir (path_to_watch)])
      added = [f for f in new_path_contents if not f in old_path_contents]
      deleted = [f for f in old_path_contents if not f in new_path_contents]
      if added: print "Added: ", ", ".join (added)
      if deleted: print "Deleted: ", ", ".join (deleted)

      old_path_contents = new_path_contents
      win32file.FindNextChangeNotification (change_handle)

finally:
  win32file.FindCloseChangeNotification (change_handle)
