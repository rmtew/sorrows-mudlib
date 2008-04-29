# Bootstrapping code.
import sys, os, stackless, gc

def Run():
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
    # Disable the built-in socket polling.
    stacklesssocket.managerRunning = True
    stacklesssocket.install()

    # Monkey-patch in the BeNice function as 'stackless.schedule' for the
    # 'stacklesssocket' module to use.
    import uthread
    stacklesssocket._schedule = uthread.BeNice

    # Add the "livecoding" contrib directory to the path.
    livecodingDirPath = os.path.join(dirPath, "contrib", "livecoding")
    if os.path.exists(livecodingDirPath):
        sys.path.append(livecodingDirPath)

    # Register the mudlib and game script directories with the livecoding
    # module.  This will compile and execute them all.
    import livecoding
    gameScriptPath = os.path.join(dirPath, "game - example")
    mudlibScriptPath = os.path.join(dirPath, "mudlib")
    cc = livecoding.CodeManager(detectChanges=True)
    cc.AddDirectory(mudlibScriptPath, "mudlib")
    cc.AddDirectory(gameScriptPath, "game")
    
    import imp, __builtin__
    __builtin__.sorrows = imp.new_module('sorrows')

    from mudlib.services import ServiceService
    svcSvc = ServiceService()
    svcSvc.gameScriptPath = "game - example"
    svcSvc.gameDataPath = os.path.join("game - example", "data")
    svcSvc.Register()
    svcSvc.Start()
    del svcSvc
    
    stackless.getcurrent().block_trap = False

    servicesStopping = True
    while True:
        try:
            try:
                uthread.Run()
            except KeyboardInterrupt:
                print
                print '** EXITING: Server manually stopping.'
                print
        finally:
            if servicesStopping is True:
                servicesStopping = 10
                # Clear the only reference to the live coding module.  File change notifications
                # at this point serve no purpose but confusion.
                del cc
                # Kill the sleeping tasklets remaining.
                uthread.KillSleepingTasklets()
                # Tell all the services to stop.
                uthread.new(sorrows.services.Stop) 
            elif servicesStopping:
                servicesStopping -= 1
            else:
                break

if __name__ == '__main__':
    Run()

