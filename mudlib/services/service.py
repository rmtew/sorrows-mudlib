from mudlib import Service
import types
import stackless
import uthread

# Types of events to broadcast:
# SendEventNow  - Deliver the event to all listeners and block while doing it.
# SendEvent     - Deliver the event to all listeners in our own time.

class ServiceService(Service):
    __sorrows__ = 'services'

    def Run(self):
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
        self.RunPendingServices(pendingList)

        # Now possibly start the specified optional services.
        # We have to do them separately because the data service is an obligatory service and it needs to be started first.
        pendingList = []
        services = sorrows.data.config.services
        for v in optionalList:
            if services.getint(v.__sorrows__, 0):
                pendingList.append(v)
        if len(pendingList):
            self.RunPendingServices(pendingList)

        self.AddEventListener(self)

        # Install the event built-ins.
        import __builtin__
        __builtin__.SendEvent = dom = self.SendEvent
        __builtin__.SendEventNow = dom = self.SendEventNow

        SendEvent('OnServicesStarted')

    def RunPendingServices(self, pendingList):
        cnt = 20
        skips = 0
        while len(pendingList):
            stillPendingList = []
            for svcClass in pendingList:
                start = 1
                for svcName2 in getattr(svcClass, '__dependencies__', []):
                    if not self.runningServices.has_key(svcName2):
                        start = 0
                        break
                if start:
                    self.StartService(svcClass())
                else:
                    stillPendingList.append(svcClass)
                    skips += 1
            pendingList = stillPendingList
        if not cnt:
            self.LogError("Unable to start services: %s", [ x.__sorrows__ for x in pendingList ])
        else:
            self.LogInfo("(held off %d starts due to dependencies in the process, tries left %d)", skips, cnt)

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
        self.LogInfo("Starting sorrows."+ svcName)

        svc.Register()
        svc.Start()

        for svcName2 in getattr(svc, '__dependencies__', []):
            if not self.dependenciesByService.has_key(svcName2):
                self.dependenciesByService[svcName2] = []
            self.dependenciesByService[svcName2].append(svcName)

        self.runningServices[svcName] = svc
        self.AddEventListener(svc)

    def StopService(self, svc):
        svcName = svc.__sorrows__
        self.LogInfo("Stopping sorrows."+ svcName)

        for svcName2 in getattr(svc, '__dependencies__', []):
            if self.dependenciesByService.has_key(svcName2):
                self.dependenciesByService[svcName2].remove(svcName)
                if not len(self.dependenciesByService[svcName2]):
                    del self.dependenciesByService[svcName2]

        self.RemoveEventListener(svc)
        del self.runningServices[svcName]

        svc.Stop()
        svc.Unregister()

    # ------------------------------------------------------------------------
    # Event support.

    def AddEventListener(self, ob):
        for eventName in getattr(ob, '__listenevents__', []):
            if not self.listenersByEvent.has_key(eventName):
                self.listenersByEvent[eventName] = []
            self.listenersByEvent[eventName].append(ob)

    def RemoveEventListener(self, ob):
        for eventName in getattr(ob, '__listenevents__', []):
            self.listenersByEvent[eventName].remove(ob)

    def SendEvent(self, eventName, *args):
        # No point in sending, if there are no listeners.
        if eventName in self.listenersByEvent:
            uthread.new(self.DeliverEvent, eventName, args)

    def SendEventNow(self, eventName, *args):
        self.DeliverEvent(eventName, args)

    def DeliverEvent(self, eventName, args):
        for listener in self.listenersByEvent.get(eventName, []):
            f = getattr(listener, eventName, None)
            f is not None and f(*args)
