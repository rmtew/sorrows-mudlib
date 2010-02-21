import textsupport
from mudlib import PlayerCommand

class Commands(PlayerCommand):
    __verbs__ = [ 'commands' ]

    def Run(self, verb, arg):
        d =  sorrows.commands.List(self.shell)
        write = self.shell.user.Tell

        playerCommands = d.get("player", [])

        if len(playerCommands):
            playerCommands.sort()

            write("Player commands:")
            write(textsupport.hcolumns(playerCommands, width=self.shell.user.connection.consoleColumns))
        
        developerCommands = d.get("developer", [])

        if len(developerCommands):
            developerCommands.sort()

            write("Developer commands:")
            write(textsupport.hcolumns(developerCommands, width=self.shell.user.connection.consoleColumns))
