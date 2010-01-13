from mudlib import Service
import types, random, weakref
import stackless
import uthread

# Types of events to broadcast:
# SendEventNow  - Deliver the event to all listeners and block while doing it.
# SendEvent     - Deliver the event to all listeners in our own time.

class ServiceService(Service):
    __sorrows__ = 'services'

    def Run(self):
        self.listeners = weakref.WeakValueDictionary()
        self.listenersByEvent = {}
        self.dependenciesByService = {}

        # Find all the services in under the mudlib or game code.
        from mudlib import IsServiceLoaded, Service, services
        serviceItems = services.__dict__.items()
        from game import services
        serviceItems.extend(services.__dict__.items())

        # Creating instances installs the services in the sorrows namespace.
        self.runningServices = {}

        # Determine which services have to start and which can optionally be started if the config specifies they should be.
        pendingList = []
        optionalList = []
        for k, v in serviceItems:
            if v is Service or IsServiceLoaded(v):
                continue
            if type(v) is not types.ClassType:
                continue
            if issubclass(v, Service):
                if v.__optional__:
                    optionalList.append(v)
                else:
                    pendingList.append(v)

        # Start the obligatory services.
        if not self.RunPendingServices(pendingList):
            # TODO: Handle this better?
            return

        # Now possibly start the specified optional services.
        # We have to do them separately because the data service is an obligatory service and it needs to be started first.
        services = sorrows.data.config.services
        pendingList = [ v for v in optionalList if services.getint(v.__sorrows__, False) ]
        if len(pendingList):
            # TODO: Also handle this better?
            self.RunPendingServices(pendingList)

        events.launch.ServicesStarted()

    def RunPendingServices(self, pendingList):
        self.LogInfo("Starting %d services", len(pendingList))

        lastDependencyIndex = None
        retryCount = 0
        while len(pendingList):
            dependencyIndex = {}
            for svcClass in pendingList:
                serviceDependencies = svcClass.__dependencies__ - set(self.runningServices.iterkeys())
                if serviceDependencies:
                    dependencyIndex[svcClass] = serviceDependencies
                    continue

                self.StartService(svcClass())

            if dependencyIndex == lastDependencyIndex:
                # Note that no progress was made.
                retryCount += 1
                # Give up after a given number of tries.
                if retryCount == 10:
                    self.LogError("Service startup procedure failed.")
                    return False

                # As long as we keep retrying, try some variation.
                random.shuffle(pendingList)
            else:
                retryCount = 0

            lastDependencyIndex = dependencyIndex
            pendingList = dependencyIndex.keys()

        return True

    def OnStop(self):
        cnt = 20
        skips = 0
        while len(self.runningServices) and cnt:
            for svcName, svc in self.runningServices.items():
                # Do not stop the current service if it has running dependencies.
                matches = [
                    svcName2
                    for svcName2 in self.dependenciesByService.get(svcName, [])
                    if self.runningServices.has_key(svcName2)
                ]
                if not len(matches):
                    self.StopService(svc)
                else:
                    skips += 1
                # Give tasklets that are no longer valid due to the stopping of their
                # service a chance to exit before further services in the dependency
                # order are stopped next.
                uthread.BeNice()
            cnt -= 1
        if not cnt:
            self.LogError("Unable to stop services: %s", self.runningServices.keys())
        else:
            self.LogInfo("(held off %d stops due to dependencies in the process, tries left %d)", skips, cnt)

    def StartService(self, svc):
        svcName = svc.__sorrows__
        self.LogInfo("Starting sorrows.%s", svcName)

        svc.Register()
        svc.Start()

        for svcName2 in svc.__dependencies__:
            if not self.dependenciesByService.has_key(svcName2):
                self.dependenciesByService[svcName2] = []
            self.dependenciesByService[svcName2].append(svcName)

        self.runningServices[svcName] = svc

    def StopService(self, svc):
        svcName = svc.__sorrows__
        self.LogInfo("Stopping sorrows.%s", svcName)

        for svcName2 in svc.__dependencies__:
            if self.dependenciesByService.has_key(svcName2):
                self.dependenciesByService[svcName2].remove(svcName)
                if not len(self.dependenciesByService[svcName2]):
                    del self.dependenciesByService[svcName2]

        del self.runningServices[svcName]

        svc.Stop()
        svc.Unregister()

