
import time
from livecoding import reloader

# You can uncomment the following lines to see further detail.
#import logging
#logging.basicConfig(level=logging.DEBUG)

def Run():
    cr = reloader.CodeReloader()
    cr.AddDirectory("base", "scripts")

    # The 'base' namespace is now available.    
    import base

    lastReturnValue = None
    while 1:
        ret = base.Function()
        if lastReturnValue is None:
            print "Initial function return value", ret
        elif ret != lastReturnValue:
            print "Updated function return value", ret
        else:
            print "Unchanged function return value", ret

        lastReturnValue = ret

        time.sleep(3.0)

if __name__ == "__main__":
    Run()
