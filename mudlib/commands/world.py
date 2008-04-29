from mudlib import WorldCommand

class WorldCmd(WorldCommand):
    __verbs__ = [ 'world' ]

    def Run(self, verb, arg):
        # Go through all the services and list each one that has
        # a name prefixed with world.

        candidates = [ k for k in dir(sorrows) if len(k) > 5 and k.startswith("world") ]

        if len(arg) == 0:
            svcName = self.shell.user.worldServiceName
            if svcName is None:
                self.shell.user.Tell('You are not currently within a world.')
            else:
                self.shell.user.Tell('You are currently within the world: "%s"' % svcName)
            self.shell.user.Tell("")

            self.shell.user.Tell('Available world models:')
            for s in candidates:
                self.shell.user.Tell("  "+ s)
            self.shell.user.Tell("")

            self.shell.user.Tell('Usage: world <model-name>')
        else:
            if arg in candidates:
                if arg == self.shell.user.worldServiceName:
                    self.shell.user.Tell('You are already present within "%s", feel free to look around.' % arg)
                else:
                    if self.shell.user.worldServiceName:
                        svc = self.GetWorldService()
                        svc.RemoveUser(self.shell.user)
                    self.shell.user.worldServiceName = arg
                    svc = self.GetWorldService()
                    svc.AddUser(self.shell.user)
                    self.shell.user.Tell('You are now present within "%s", feel free to look around.' % arg)
            else:
                self.shell.user.Tell('Desired world model not found: '+ arg)
