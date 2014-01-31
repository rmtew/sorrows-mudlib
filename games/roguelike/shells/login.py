import logging, stackless
from stacklesslib.main import sleep as tasklet_sleep
from mudlib import InputHandler
import mudlib.shells
from game import Shell

logger = logging.getLogger("net")

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

STATE_CLIENT_EXAM = "CLIENT_EXAM"
STATE_GET_LOGIN_NAME = "GET_LOGIN_NAME"
STATE_GET_PASSWORD = "GET_PASSWORD"
STATE_CREATE_PASSWORD1 = "CREATE_PASSWORD1"
STATE_CREATE_PASSWORD2 = "CREATE_PASSWORD2"
STATE_GET_CHARACTER = "GET_CHARACTER"

PASSWORD_STATES = set([ STATE_GET_PASSWORD, STATE_CREATE_PASSWORD1, STATE_CREATE_PASSWORD2 ])

loginPrompts = {
    STATE_CLIENT_EXAM:          "",
    STATE_GET_LOGIN_NAME:       "Login name: ",
    STATE_GET_PASSWORD:         "Password: ",
    STATE_CREATE_PASSWORD1:     "Password: ",
    STATE_CREATE_PASSWORD2:     "Password (again): ",
    STATE_GET_CHARACTER:        "ERROR - NOT YET IMPLEMENTED",
}

MIN_USERNAME_SIZE = 3
MAX_USERNAME_SIZE = 12

MIN_PASSWORD_SIZE = 6
MAX_PASSWORD_SIZE = 20

CTRL_E                = chr(5)  # ENQ


class LoginShell(Shell):
    state = STATE_CLIENT_EXAM

    def Setup(self, stack):
        Shell.Setup(self, stack)

        self.userName = None
        self.password = None
        
        self.oldOptionLineMode = None

        handler = InputHandler()
        handler.Setup(self, self.ReceiveInput, None, 0)
        self.stack.SetShell(handler)

        # Send telnet negotiation, but don't block this.
        
        stackless.tasklet(self.StartClientExam)()

    def StartClientExam(self):
        def _wait_func(channel, seconds):
            tasklet_sleep(seconds)
            channel.send(None)
        channel1 = stackless.channel()
        def _terminaltype_cb(terminalTypeName):
            channel1.send(terminalTypeName)
        self.user.connection.telneg_terminaltype_cb = _terminaltype_cb

        telneg = self.user.connection.telneg
        telneg.will_sga()        
        telneg.will_echo()
        telneg.do_naws()
        telneg.do_new_environ()
        telneg.do_ttype()

        # Wait for the soonest of a terminal type, give up after a short delay.
        stackless.tasklet(_wait_func)(channel1, 1.0)
        terminalTypeName = channel1.receive()
        
        if terminalTypeName:
            self.user.connection.SetClientName(terminalTypeName)
            if self.EndClientExam():
                self._WritePrompt()
            return

        # Ask the client terminal what their name is.
        self.oldOptionLineMode = self.user.connection.SetLineMode(False)
        self.user.connection.SetPasswordMode(True)
        self.user.Write(CTRL_E)

        tasklet_sleep(1.0)
        if self.EndClientExam():
            self._WritePrompt()

    def EndClientExam(self):
        if self.state == STATE_CLIENT_EXAM:
            self.state = STATE_GET_LOGIN_NAME

            mudName = sorrows.data.config.identity.name
            if False and self.user.connection.clientName:
                # Set client window title.
                # self.user.Write("\x1b]2;%s\x07" % mudName)
                # Enable mouse events.
                self.user.Write("\x1b[?1003h")
            if self.oldOptionLineMode is not None:
                self.user.connection.SetLineMode(self.oldOptionLineMode)
                self.oldOptionLineMode = None
            self.user.connection.SetPasswordMode(False)
            # Print a login screen here if so desired.
            self.user.Tell(mudName)
            self.user.Tell("Enter 'quit' or 'q' at any time during the login process to disconnect.\n")
            return True
        return False

    def DispatchInputSequence(self, s):
        s = s.strip()
        if s == 'q' or s == 'quit':
            return self.user.ManualDisconnection()

        #print "DispatchInputSequence", s
        if self.state == STATE_CLIENT_EXAM:
            self.user.connection.SetClientName(s)
            self.EndClientExam()
        elif self.state == STATE_GET_LOGIN_NAME:
            userName = s
            if sorrows.users.UserExists(userName):
                self.user.Tell("Hello again.")
                self.userName = userName
                self.guessAttempts = 3
                self.state = STATE_GET_PASSWORD
            elif len(userName) < MIN_USERNAME_SIZE:
                self.user.Tell("That account name is too short.  Minimum length is %d characters." % MIN_USERNAME_SIZE)
            elif len(userName) > MAX_USERNAME_SIZE:
                self.user.Tell("That account name is too long.  Maximum length is %d characters." % MAX_USERNAME_SIZE)
            else:
                self.user.Tell("Creating a new account with the name '"+ userName +"'.")
                self.userName = userName
                self.state = STATE_CREATE_PASSWORD1
        elif self.state == STATE_CREATE_PASSWORD1:
            password = s
            self.user.Tell("")
            if len(password) < MIN_PASSWORD_SIZE:
                self.user.Tell("That password is too short.  Minimum length is %d characters." % MIN_PASSWORD_SIZE)
            elif len(password) > MAX_PASSWORD_SIZE:
                self.user.Tell("That password is too long.  Maximum length is %d characters." % MAX_PASSWORD_SIZE)
            else:
                self.password = password
                self.state = STATE_CREATE_PASSWORD2
        elif self.state == STATE_CREATE_PASSWORD2:
            password = s
            self.user.Tell("")
            if password != self.password:
                self.user.Tell("That password does not match.  Try again.")
                self.state = STATE_CREATE_PASSWORD1
            else:
                try:
                    sorrows.users.Add(self.userName, self.password)
                    self.user.connection.SetPasswordMode(False)
                    #self.state = "SelectCharacter"

                    return self.EnterGame()
                except Exception:
                    self.user.Tell("Someone created an account with that name while you were in the process of creating yours.")
                    self.state = STATE_GET_LOGIN_NAME
                    logging.exception(STATE_CREATE_PASSWORD2)
        elif self.state == STATE_GET_PASSWORD:
            self.user.Tell("")
            if sorrows.users.CheckPassword(self.userName, s):
                self.user.connection.SetPasswordMode(False)

                return self.EnterGame()
            elif self.guessAttempts > 1:
                self.guessAttempts -= 1
            else:
                return self.user.ManualDisconnection()

        self._WritePrompt()

    def _WritePrompt(self):
        if self.state in PASSWORD_STATES:
            self.user.connection.SetPasswordMode(True)
        self.user.Write(loginPrompts[self.state])

    def EnterGame(self):
        self.user.name = self.userName

        isDeveloper = getattr(sorrows.data.config.developers, self.userName, False)
        if isDeveloper:
            mudlib.shells.DeveloperGameShell().Setup(self.stack)
        else:
            mudlib.shells.GameShell().Setup(self.stack)

    def OnRemovalFromStack(self):
        if self.user.connection.connected:
            if self.oldOptionLineMode is not None:
                self.user.connection.SetLineMode(self.oldOptionLineMode)
        Shell.OnRemovalFromStack(self)
