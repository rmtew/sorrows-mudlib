# Bootstrapping code.
import sys, os, stackless, gc, logging, traceback

# TODO: Not getting class creation events yet.

def OnClassAddition(class_):
    print "CREATE", class_

def OnClassUpdate(class_):
    #import pysupport
    gc.collect()
    for instanceClass, instances in pysupport.FindInstances(class_).iteritems():
        print "FOUND INSTANCES", instanceClass, instances
        # for instance in instances:
        #    pysupport.PrintReferrers(instance)


def Run():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s;%(name)s;%(levelname)s;%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

    logging.getLogger().name = "default"
    logging.getLogger("namespace").setLevel(logging.INFO)
    logging.getLogger("reloader").setLevel(logging.INFO)

    stackless.getcurrent().block_trap = True

    dirPath = sys.path[0]
    if not len(dirPath):
        raise RuntimeError("Expected to find the directory the script was executed in in sys.path[0], but did not.")

    iniFilename = os.path.join(dirPath, "config.ini")
    if not os.path.exists(iniFilename):
        print "Please copy 'config.ini.base' to 'config.ini' and modify it appropriately."
        sys.exit(0)

    # Add the "contrib" directory to the path.
    contribDirPath = os.path.join(dirPath, "contrib")
    if os.path.exists(contribDirPath):
        sys.path.append(contribDirPath)

    # Monkey-patch in the stackless-compatible sockets.
    import stacklesssocket
    import uthread, uthread2
    stacklesssocket._schedule = uthread.BeNice
    stacklesssocket.install()

    # Add the "livecoding" contrib directory to the path.
    livecodingDirPath = os.path.join(dirPath, "contrib", "livecoding")
    if os.path.exists(livecodingDirPath):
        sys.path.append(livecodingDirPath)

    # Register the mudlib and game script directories with the livecoding
    # module.  This will compile and execute them all.
    import reloader
    gamePath = os.path.join("games", "room - simple")
    gameScriptPath = os.path.join(dirPath, gamePath)
    mudlibScriptPath = os.path.join(dirPath, "mudlib")

    cr = reloader.CodeReloader(mode=reloader.MODE_UPDATE)
    # Register for code reloading updates of managed classes.
    # Broadcast an event when we receive an update.
    cr.SetClassUpdateCallback(OnClassUpdate)
    cr.AddDirectory("mudlib", mudlibScriptPath)
    cr.AddDirectory("game", gameScriptPath)

    import imp, __builtin__
    from events import EventHandler
    __builtin__.events = EventHandler()
    __builtin__.sorrows = imp.new_module('sorrows')

    from mudlib.services import ServiceService
    svcSvc = ServiceService()
    svcSvc.gameScriptPath = gamePath
    svcSvc.gameDataPath = os.path.join(gamePath, "data")
    svcSvc.Register()
    svcSvc.Start()
    del svcSvc
    
    stackless.getcurrent().block_trap = False

    manualShutdown = False
    try:
        uthread.Run()
    except KeyboardInterrupt:
        print
        print '** EXITING: Server manually stopping.'
        print
        manualShutdown = True
    finally:
        cr.EndMonitoring()

    if manualShutdown:
        class HelperClass:
            def ShutdownComplete(self):
                managerTasklet.kill()

        helper = HelperClass()
        events.ShutdownComplete.Register(helper.ShutdownComplete)

        uthread.new(sorrows.services.Stop)
        # We have most likely killed the stacklesssocket tasklet.
        managerTasklet = stacklesssocket.StartManager()
        uthread.Run()

    logging.info("Shutdown complete")


if __name__ == '__main__':
    try:
        Run()
    finally:
        logging.shutdown()

