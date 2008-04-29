from mudlib import Command

class WorldCommand(Command):
    def GetWorldService(self):
        svcName = self.shell.user.worldServiceName
        if svcName is None:
            raise RuntimeError("Bad world service name", svcName)
        svc = getattr(sorrows, svcName, None)
        if svc is None:
            raise RuntimeError("Bad world service", svcName)
        return svc
