import logging, cPickle

STATE_STARTING = 1
STATE_STARTED = 2
STATE_STOPPING = 3
STATE_STOPPED = 4

def IsServiceLoaded(serviceClass):
    serviceName = getattr(serviceClass, '__sorrows__', None)
    if serviceName is not None:
        if hasattr(sorrows, serviceName):
            return 1
    return 0

class Service:
    # The current state of the service as managed by us, ideally.
    state = None
    # Whether the service should be automatically run when loaded.
    __optional__ = False

    def Release(self):
        pass

    def Register(self):
        serviceName = getattr(self, '__sorrows__', None)
        if serviceName is not None:
            if hasattr(sorrows, serviceName):
                raise RuntimeError('Our evil twin beat us here..', getattr(sorrows, serviceName))
            setattr(sorrows, serviceName, self)

    def Unregister(self):
        serviceName = getattr(self, '__sorrows__', None)
        if serviceName is not None:
            check = getattr(sorrows, serviceName)
            if check is not self:
                raise RuntimeError('Found our evil twin..', check)
            delattr(sorrows, serviceName)

    def IsRegistered(self):
        serviceName = getattr(self, '__sorrows__', None)
        if serviceName is not None:
            return getattr(sorrows, serviceName, None) is self
        return 0

    def Start(self):
        if not self.IsRegistered():
            raise RuntimeError('Service is not registered')
        if self.state is None:
            self.Setup()
        elif self.state != STATE_STOPPED:
            raise RuntimeError('Service in unexpected state', self.state)
        self.state = STATE_STARTING
        self.Run()
        self.state = STATE_STARTED

    def Setup(self):
        pass

    def Run(self):
        pass

    def Stop(self):
        if self.state != STATE_STARTED:
            raise RuntimeError('Service in unexpected state', self.state)
        self.state = STATE_STOPPING
        self.OnStop()
        self.state = STATE_STOPPED

    def OnStop(self):
        pass

    # =======================================================================

    def IsStarting(self):
        return self.state == STATE_STARTING

    def IsRunning(self):
        return self.state == STATE_STARTED

    def IsStopping(self):
        return self.state == STATE_STOPPING

    # =======================================================================

    def UnpersistData(self, path):
        try:
            f = open(path, 'rb')
            d = cPickle.load(f)
            f.close()
        except IOError, e:
            if e.errno == 2:
                return {}
            else:
                raise
        return d

    def PersistData(self, path, d):
        f = open(path, 'wb')
        cPickle.dump(d, f, 1)
        f.close()


    # ------------------------------------------------------------------------
    # Logging support.

    def LogInfo(self, *args):
        self.Log(args, level=logging.INFO)

    def LogWarning(self, *args):
        self.Log(args, level=logging.WARNING)

    def LogError(self, *args):
        self.Log(args, level=logging.ERROR)

    def Log(self, args, level=logging.INFO):
        svc = self.__sorrows__
        if len(svc) < 8:
            svc += "\t"
        msg = svc +"\t"+ " ".join([ str(value) for value in args])
        logging.log(level, msg)

