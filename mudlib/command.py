COMMAND_PLAYER    = 1
COMMAND_GAME      = 2
COMMAND_DEVELOPER = 4

commandLabels = [
    ("player",    COMMAND_PLAYER),
    ("game",      COMMAND_GAME),
    ("developer", COMMAND_DEVELOPER),
]

commandLabelsByAccessMask = {
    COMMAND_PLAYER:    "player",
    COMMAND_GAME:      "game",
    COMMAND_DEVELOPER: "developer",
}


class BaseCommand:
    def __init__(self):
        raise Exception("This class should not be instantiated")

    @staticmethod
    def Run(context):
        pass


class PlayerCommand(BaseCommand):
    __access__ = COMMAND_PLAYER


class GameCommand(PlayerCommand):
    __access__ = COMMAND_GAME

    @staticmethod
    def Run(context):
        sorrows.parser.ExecuteGameCommand(context)


class DeveloperCommand(BaseCommand):
    __access__ = COMMAND_DEVELOPER


class CommandContext:
    def __init__(self, commandClass, verb, argString, shell):
        self.commandClass = commandClass
        self.userAccessMask = shell.__access__

        self.verb = verb
        self.argString = argString

        self.user = shell.user
        self.body = self.user.body
        self.room = self.body.container

