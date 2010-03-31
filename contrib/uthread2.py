"""
uthread2.py
Copyright (C) 2010  Richard Tew

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import traceback, stackless

def PrintChannel(c):
    """ Print a readable summary of the channel state. """
    print "CHANNEL:", c, "balance:", c.balance

    tasklet = c.queue
    idx = 0
    while tasklet is not None:
        print "  TASKLET %3d:" % idx, tasklet
        traceback.print_stack(tasklet.frame)

        tasklet = tasklet.next
        idx += 1

def PrintTaskletChain(tasklet):
    """ xxx """
    idx = 0
    seen = {}
    while tasklet and tasklet not in seen:
        # Can't print main, as it has a cframe or something.
        if tasklet is not stackless.main:
            print "  TASKLET %3d:" % idx, tasklet
            traceback.print_stack(tasklet.frame)        
        else:
            print "  TASKLET %3d (MAIN):" % idx, tasklet
            idx += 1

        seen[tasklet] = True
        tasklet = tasklet.next
