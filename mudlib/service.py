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
    # Dependencies.
    __dependencies__ = frozenset()
    # Whether the service should be automatically run when loaded.
    __optional__ = False
    # The custom logger object.
    logger = None

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

    # Logging support.

    def LogException(self, *args, **kwargs):
        if self.logger is None:
            self.logger = logging.getLogger(self.__sorrows__)
        
        self.logger.exception(*args, **kwargs)

    def LogInfo(self, *args, **kwargs):
        self.Log(logging.INFO, *args, **kwargs)

    def LogWarning(self, *args, **kwargs):
        self.Log(logging.WARNING, *args, **kwargs)

    def LogError(self, *args, **kwargs):
        self.Log(logging.ERROR, *args, **kwargs)

    def LogDebug(self, *args, **kwargs):
        self.Log(logging.DEBUG, *args, **kwargs)

    def Log(self, level, *args, **kwargs):
        if self.logger is None:
            self.logger = logging.getLogger(self.__sorrows__)

        self.logger.log(level, *args, **kwargs)

