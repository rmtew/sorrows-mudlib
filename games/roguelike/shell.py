# Akin to terminal support.  Extracts and reacts to escape sequences, before processing text.

import stackless
from stacklesslib.main import sleep as tasklet_sleep
import mudlib

ESC = chr(27)

# Escape termination characters.
#
# The rule for detecting a full escape sequence is to keep reading characters
# after escape until any character from 'a'-'z', '{', '|', '@', 'A'-'Z' is
# encountered.

ESC_TERMINATORS = set()
for v in range(97, 124+1):
    ESC_TERMINATORS.add(chr(v))
for v in range(64, 90+1):
    ESC_TERMINATORS.add(chr(v))


class Shell(mudlib.Shell):
    def Setup(self, stack):
        mudlib.Shell.Setup(self, stack)

        self.inputBuffer = ""
        self.escapeTasklet = None

    def ReceiveInput(self, s, flush=False):
        if False:
            cnt = getattr(self, "xxx", 1)
            self.xxx = cnt + 1
            print cnt, "** ReceiveInput", [ ord(c) for c in s ], flush
 
        if len(self.inputBuffer):
            s = self.inputBuffer + s
            self.inputBuffer = ""

        escapeTasklet = self.escapeTasklet
        self.escapeTasklet = None

        if not flush:
            if escapeTasklet:
                escapeTasklet.kill()

            if s[0] == ESC:
                if len(s) == 1:
                    self.inputBuffer = s

                    # Might be a keypress or the start of an escape sequence.
                    # The way to differentiate is to use a timeout to wait for
                    # the rest of the escape sequence, and if nothing arrives 
                    # to assume it is a keypress.
                    self.escapeTasklet = stackless.tasklet(self.ReceiveInput_EscapeTimeout)()
                    return

                if s[1] != '[':
                    idx = s.find(ESC, 1)
                    if idx == -1:
                        self.DispatchInputSequence(s)
                        return
                    self.DispatchInputSequence(s[:idx])
                    self.ReceiveInput(s[idx:])
                    return

                for i, c in enumerate(s):
                    if c in ESC_TERMINATORS:
                        self.DispatchInputSequence(s[:i+1])
                        remainingInput = s[i+1:]
                        if remainingInput:
                            self.ReceiveInput(remainingInput)
                        return

                self.inputBuffer = s
                return

        idx = s.find(ESC)
        if idx == -1 or idx == 0:
            self.DispatchInputSequence(s)
        else:
            self.DispatchInputSequence(s[:idx])
            self.ReceiveInput(s[idx:])
        # print "** ReceiveInput - DONE"

    def ReceiveInput_EscapeTimeout(self):
        tasklet_sleep(0.1)
        self.ReceiveInput("", flush=True)

    def DispatchInputSequence(self, text):
        pass
