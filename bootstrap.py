# Bootstrapping code.
import sys, os, stackless, gc, logging, traceback, types

dirPath = sys.path[0]
if not len(dirPath):
    raise RuntimeError("Expected to find the directory the script was executed in in sys.path[0], but did not.")

# Add the "contrib" directory to the path.
contribDirPath = os.path.join(dirPath, "contrib")
if os.path.exists(contribDirPath) and contribDirPath not in sys.path:
    sys.path.append(contribDirPath)

import pysupport

STATE_STARTUP = 0
STATE_RUNNING = 1
STATE_SHUTDOWN = 2

bootstrapState = STATE_STARTUP

def OnClassCreation(class_):
    class_.__instances__ = classmethod(pysupport.FindClassInstances)
    if not hasattr(class_, "__subclasses__"):
        class_.__subclasses__ = classmethod(pysupport.FindClassSubclasses)

    class_.__events__ = set()

    if bootstrapState != STATE_STARTUP:
        print "CREATE", class_

    events.ProcessClass(class_)

    if bootstrapState != STATE_STARTUP:
        events.ClassCreation(class_)

def OnClassUpdate(class_):
    if bootstrapState != STATE_STARTUP:
        gc.collect()
        instances = pysupport.FindInstances(class_)
        instanceCount = sum(len(l) for l in instances.itervalues())
        print "UPDATE", class_, instanceCount, "instances"

    events.ProcessClass(class_)

    if bootstrapState != STATE_STARTUP:
        events.ClassUpdate(class_)

def OnScriptValidation(scriptFile):
    try:
        from mudlib import GameCommand
    except ImportError:
        return

    # TODO: Make this more generic.
    for k, v in scriptFile.scriptGlobals.iteritems():
        if type(v) in (types.ClassType, types.TypeType) and v is not GameCommand:
            if issubclass(v, GameCommand) and "Run" in v.__dict__:
                raise Exception("Subclasses of GameCommand cannot override Run")

def Run():
    global bootstrapState

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s;%(name)s;%(levelname)s;%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

    logging.getLogger().name = "default"
    logging.getLogger("namespace").setLevel(logging.INFO)
    logging.getLogger("reloader").setLevel(logging.INFO)

    stackless.getcurrent().block_trap = True

    iniFilename = os.path.join(dirPath, "config.ini")
    if not os.path.exists(iniFilename):
        print "Please copy 'config.ini.base' to 'config.ini' and modify it appropriately."
        sys.exit(0)

    # Monkey-patch in the stackless-compatible sockets.
    import stacklesssocket
    import uthread, uthread2
    stacklesssocket._schedule_func = uthread.BeNice
    stacklesssocket._sleep_func = uthread.Sleep
    stacklesssocket.install()

    # Install the global event handler.
    import __builtin__
    from events import EventHandler
    __builtin__.events = EventHandler()

    # Add the "livecoding" contrib directory to the path.
    livecodingDirPath = os.path.join(dirPath, "contrib", "livecoding")
    if os.path.exists(livecodingDirPath):
        sys.path.append(livecodingDirPath)

    # Register the mudlib and game script directories with the livecoding
    # module.  This will compile and execute them all.
    import reloader
    #gamePath = os.path.join("games", "room - simple")
    gamePath = os.path.join("games", "roguelike")
    gameScriptPath = os.path.join(dirPath, gamePath)
    mudlibScriptPath = os.path.join(dirPath, "mudlib")

    cr = reloader.CodeReloader()
    # Register for code reloading updates of managed classes.
    # Broadcast an event when we receive an update.
    cr.SetClassCreationCallback(OnClassCreation)
    cr.SetClassUpdateCallback(OnClassUpdate)
    cr.SetValidateScriptCallback(OnScriptValidation)
    cr.AddDirectory("mudlib", mudlibScriptPath)
    cr.AddDirectory("game", gameScriptPath)

    import imp
    __builtin__.sorrows = imp.new_module('sorrows')

    from mudlib.services import ServiceService
    svcSvc = ServiceService()
    svcSvc.gameScriptPath = gamePath
    svcSvc.gameDataPath = os.path.join(gamePath, "data")
    svcSvc.Register()
    svcSvc.Start()
    del svcSvc
    
    stackless.getcurrent().block_trap = False
    bootstrapState = STATE_RUNNING

    manualShutdown = False
    try:
        uthread.Run()
    except KeyboardInterrupt:
        print
        print '** EXITING: Server manually stopping.'
        print
        
        if stackless.runcount > 1:
            print "Scheduled tasklets:", stackless.runcount
            uthread2.PrintTaskletChain(stackless.current)
            print

        if uthread.yieldChannel.queue:
            print "Yielded tasklets:"
            uthread2.PrintTaskletChain(uthread.yieldChannel.queue)
            print

        for timestamp, channel in uthread.sleepingTasklets:
            if channel.queue:
                print "Sleep channel (%d) tasklets:" % id(channel)
                uthread2.PrintTaskletChain(channel.queue)
                print

        manualShutdown = True
    finally:
        cr.EndMonitoring()

    bootstrapState = STATE_SHUTDOWN

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

