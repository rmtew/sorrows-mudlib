import logging
import uthread
from mudlib import InputHandler, Shell
import mudlib.shells

# TODO: Rewrite this to detect graphical capability and to handle it appropriately.

# Enter login name.
# - User exists.
#   - Enter password (3 attempts).
# - User does not exist.
#   - Ask if they want to create the account.
#   - Enter password.
#   - Enter password again.
# - List users characters, option to create new one.
#   - Select character.
#   - Create new character.
#     - Select race.
#     - Select gender.
#     - Select age.
#     - ...

loginPrompts = {
    "EnterLoginName":       "Login name: ",
    "EnterPassword":        "Password: ",
    "CreatePassword1":      "Password: ",
    "CreatePassword2":      "Password (again): ",
    "SelectCharacter":      "Not yet implemented...",
}

MIN_USERNAME_SIZE = 3
MAX_USERNAME_SIZE = 12

MIN_PASSWORD_SIZE = 6
MAX_PASSWORD_SIZE = 20

class LoginShell(Shell):
    state = "EnterLoginName"

    def Setup(self, stack):
        Shell.Setup(self, stack)

        self.userName = None
        self.password = None

        # Print a login screen here if so desired.
        self.user.Tell(sorrows.data.config.identity.name)
        self.user.Tell("Enter 'quit' or 'q' at any time during the login process to disconnect.\n")

        handler = InputHandler()
        handler.Setup(self, self.ReceiveInput, self.WritePrompt, 0)
        self.stack.SetShell(handler)

        uthread.new(self.StartTelnetNegotiation)

    def StartTelnetNegotiation(self):
        telneg = self.user.connection.telneg
        telneg.request_naws()
        telneg.request_terminal_type()

    def ExecuteCommand(self):
        s = self.raw.strip()
        if s == 'q' or s == 'quit':
            return self.user.ManualDisconnection()

        if self.state == "EnterLoginName":
            userName = s
            if sorrows.users.UserExists(userName):
                self.user.Tell("Hello again.")
                self.userName = userName
                self.guessAttempts = 3
                self.state = "EnterPassword"
                return
            if len(userName) < MIN_USERNAME_SIZE:
                self.user.Tell("That account name is too short.  Minimum length is %d characters." % MIN_USERNAME_SIZE)
                return
            if len(userName) > MAX_USERNAME_SIZE:
                self.user.Tell("That account name is too long.  Maximum length is %d characters." % MAX_USERNAME_SIZE)
                return
            self.user.Tell("Creating a new account with the name '"+ userName +"'.")
            self.userName = userName
            self.state = "CreatePassword1"
        elif self.state == "CreatePassword1":
            password = s
            self.user.Tell("")
            if len(password) < MIN_PASSWORD_SIZE:
                self.user.Tell("That password is too short.  Minimum length is %d characters." % MIN_PASSWORD_SIZE)
                return
            if len(password) > MAX_PASSWORD_SIZE:
                self.user.Tell("That password is too long.  Maximum length is %d characters." % MAX_PASSWORD_SIZE)
                return
            self.password = password
            self.state = "CreatePassword2"
        elif self.state == "CreatePassword2":
            password = s
            self.user.Tell("")
            if password != self.password:
                self.user.Tell("That password does not match.  Try again.")
                self.state = "CreatePassword1"
                return

            try:
                sorrows.users.Add(self.userName, self.password)
            except Exception:
                self.user.Tell("Someone created an account with that name while you were in the process of creating yours.")
                self.state = "EnterLoginName"
                logging.exception("CreatePassword2")
                return

            self.user.connection.SetPasswordMode(False)
            #self.state = "SelectCharacter"

            self.EnterGame()
        elif self.state == "EnterPassword":
            self.user.Tell("")
            if sorrows.users.CheckPassword(self.userName, s):
                self.user.connection.SetPasswordMode(False)

                self.EnterGame()
            elif self.guessAttempts > 1:
                self.guessAttempts -= 1
            else:
                self.user.ManualDisconnection()

    def WritePrompt(self):
        if "Password" in self.state:
            self.user.connection.SetPasswordMode(True)
        return loginPrompts[self.state]

    def EnterGame(self):
        self.user.name = self.userName

        isDeveloper = getattr(sorrows.data.config.developers, self.userName, False)
        if isDeveloper:
            mudlib.shells.DeveloperGameShell().Setup(self.stack)
        else:
            mudlib.shells.GameShell().Setup(self.stack)
