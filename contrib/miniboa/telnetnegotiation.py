# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Modified by Richard Tew for the Sorrows Mudlib project.
#
# Obtained from:
#   http://code.google.com/p/miniboa/source/browse/trunk/miniboa/telnet.py
#------------------------------------------------------------------------------
#   miniboa/telnet.py
#   Copyright 2009 Jim Storch
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain a
#   copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#------------------------------------------------------------------------------

import logging
logger = logging.getLogger("telopt")

"""Ideally provides integratible telnet negotiation support."""

#---[ Telnet Notes ]-----------------------------------------------------------
# (See RFC 854 for more information)
#
# Negotiating a Local Option
# --------------------------
#
# Side A begins with:
#
#    "IAC WILL/WONT XX"   Meaning "I would like to [use|not use] option XX."
#
# Side B replies with either:
#
#    "IAC DO XX"     Meaning "OK, you may use option XX."
#    "IAC DONT XX"   Meaning "No, you cannot use option XX."
#
#
# Negotiating a Remote Option
# ----------------------------
#
# Side A begins with:
#
#    "IAC DO/DONT XX"  Meaning "I would like YOU to [use|not use] option XX."
#
# Side B replies with either:
#
#    "IAC WILL XX"   Meaning "I will begin using option XX"
#    "IAC WONT XX"   Meaning "I will not begin using option XX"
#
#
# The syntax is designed so that if both parties receive simultaneous requests
# for the same option, each will see the other's request as a positive
# acknowledgement of it's own.
#
# If a party receives a request to enter a mode that it is already in, the
# request should not be acknowledged.

## Where you see DE in my comments I mean 'Distant End', e.g. the client.

UNKNOWN = -1

#--[ Telnet Commands ]---------------------------------------------------------

SE      = chr(240)      # End of subnegotiation parameters
NOP     = chr(241)      # No operation
DATMK   = chr(242)      # Data stream portion of a sync.
BREAK   = chr(243)      # NVT Character BRK
IP      = chr(244)      # Interrupt Process
AO      = chr(245)      # Abort Output
AYT     = chr(246)      # Are you there
EC      = chr(247)      # Erase Character
EL      = chr(248)      # Erase Line
GA      = chr(249)      # The Go Ahead Signal
SB      = chr(250)      # Sub-option to follow
WILL    = chr(251)      # Will; request or confirm option begin
WONT    = chr(252)      # Wont; deny option request
DO      = chr(253)      # Do = Request or confirm remote option
DONT    = chr(254)      # Don't = Demand or confirm option halt
IAC     = chr(255)      # Interpret as Command
SEND    = chr(001)      # Sub-process negotiation SEND command
IS      = chr(000)      # Sub-process negotiation IS command

#--[ Telnet Options ]----------------------------------------------------------

BINARY      = chr(  0)      # Transmit Binary
ECHO        = chr(  1)      # Echo characters back to sender
RECON       = chr(  2)      # Reconnection
SGA         = chr(  3)      # Suppress Go-Ahead
TTYPE       = chr( 24)      # Terminal Type
NAWS        = chr( 31)      # Negotiate About Window Size
LINEMODE    = chr( 34)      # Line Mode
OLD_ENVIRON = chr( 36)      # Old - Environment variables
CHARSET     = chr( 42)      # 

#--[ Extra Shit ]--------------------------------------------------------------

COMPRESS1   = chr( 85)      # MCCP - Mud Client Compression Protocol, v1
COMPRESS2   = chr( 86)      # MCCP - Mud Client Compression Protocol, v2
MCP         = chr( 90)      # MSP  - Mud Sound Protocol
MXP         = chr( 91)      # MXP  - Mud eXtension Protocol

#-----------------------------------------------------------------Telnet Option

class TelnetOption(object):

    """
    Simple class used to track the status of an extended Telnet option.
    """

    def __init__(self):
        self.local_option = UNKNOWN     # Local state of an option
        self.remote_option = UNKNOWN    # Remote state of an option
        self.reply_pending = False      # Are we expecting a reply?


#------------------------------------------------------------------------Telnet

class TelnetNegotiation(object):
    """
    Represents a client connection via Telnet.

    First argument is the socket discovered by the Telnet Server.
    Second argument is the tuple (ip address, port number).

    """

    def __init__(self):
        ## State variables for interpreting incoming telnet commands
        self.telnet_got_iac = False # Are we inside an IAC sequence?
        self.telnet_got_cmd = None  # Did we get a telnet command?
        self.telnet_got_sb = False  # Are we inside a subnegotiation?
        self.telnet_opt_dict = {}   # Mapping for up to 256 TelnetOptions
        self.telnet_sb_buffer = ''  # Buffer for sub-negotiations
        
        self.terminal_types = []
        self.desired_terminal_type = None

        # Callback functions.
        self.terminal_type_selection_cb = None  # lambda termtypes: ...
        self.terminal_type_cb = None            # lambda termtype: "terminal type: %s" % termtype
        self.terminal_size_cb = None            # lambda rows, columns: "rows: %d, columns: %d" % (rows, columns)
        self.echo_cb = None                     # lambda flag: "echo" if flag else "do not echo"
        self.send_cb = None                     # lambda data: "data to be sent to the client: %s" % data
        self.compress2_cb = None                # lambda flag: "compress" if flag else "do not compress"

        # Data
        self.negotiationByteCount = 0

    def set_terminal_type_selection_cb(self, f):
        self.terminal_type_selection_cb = f

    def set_terminal_type_cb(self, f):
        self.terminal_type_cb = f

    def set_terminal_size_cb(self, f):
        self.terminal_size_cb = f

    def set_echo_cb(self, f):
        self.echo_cb = f

    def set_send_cb(self, f):
        self.send_cb = f
        
    def set_compress2_cb(self, f):
        self.compress2_cb = f

    def request_do_sga(self):
        """
        Request DE to Suppress Go-Ahead.  See RFC 858.
        """

        self._iac_do(SGA)
        self._note_reply_pending(SGA, True)

    def request_will_compress(self):
        """ Tell the DE that we would like to pack the shit we send to them. """

        self._iac_will(COMPRESS2)
        self._note_reply_pending(COMPRESS2, True)

    def request_will_echo(self):
        """ Tell the DE that we would like to echo their text.  See RFC 857. """

        self._iac_will(ECHO)
        self._note_reply_pending(ECHO, True)
        if self.echo_cb:
            self.echo_cb(True)

    def request_wont_echo(self):
        """
        Tell the DE that we would like to stop echoing their text.
        See RFC 857.
        """

        self._iac_wont(ECHO)
        self._note_reply_pending(ECHO, True)
        if self.echo_cb:
            self.echo_cb(False)

    def password_mode_on(self):

        """
        Tell DE we will echo (but don't) so typed passwords don't show.
        """

        self._iac_will(ECHO)
        self._note_reply_pending(ECHO, True)

    def password_mode_off(self):

        """
        Tell DE we are done echoing (we lied) and show typing again.
        """

        self._iac_wont(ECHO)
        self._note_reply_pending(ECHO, True)

    #def request_mccp(self):
    #    """
    #    Request to MUD Client Compression Protocol.
    #    http://mccp.smaugmuds.org/protocol.html
    #    """
    #    self._iac_do(NAWS)

    def request_mxp(self):
        """
        Request to use Mud Extension Protocol.
        http://www.zuggsoft.com/zmud/mxp.htm
        http://www.mushclient.com/mushclient/mxp.htm
        """
        self._iac_do(MXP)
        self._note_reply_pending(MXP, True)

    def request_naws(self):
        """
        Request to Negotiate About Window Size.  See RFC 1073.
        """

        self._iac_do(NAWS)
        self._note_reply_pending(NAWS, True)

    def request_terminal_type(self):
        """
        Begins the Telnet negotiations to request the terminal type from
        the remote connection.  See RFC 779.
        """

        self._iac_do(TTYPE)
        self._note_reply_pending(TTYPE, True)

    def feed(self, data):        
        """
        Parses the supplied textual data, processing any embedded negotiation
        options that are present, and yielding the actual text that it
        encounters.
        """

        # If we are not in negotiation, we may be able to just hand back text.
        if not self.telnet_got_iac and not self.telnet_got_sb:
            leading_text, option, data = data.partition(IAC)
            if leading_text:
                yield leading_text
            if option == data == "":
                return
            self._negotiation(option)

        i = 0
        for j, char in enumerate(data):
            if self._negotiation(char):
                text = data[i:j]
                if text:
                    yield text
                i = j+1

        text = data[i:j+1]
        if text:
            yield text            

    def _negotiation(self, byte):
        """
        Watches incomming data for Telnet IAC sequences.  Returns a boolean
        that indicates whether the character was negotiation related.
        """

        # logger.debug("Negotiation %d", ord(byte))

        ## Are we not currently in an IAC sequence coming from the DE?
        if self.telnet_got_iac == False:
            if byte == IAC:
                ## Well, we are now
                self.telnet_got_iac = True

            ## Are we currenty in a sub-negotion?
            elif self.telnet_got_sb == True:
                ## Sanity check on length
                if len(self.telnet_sb_buffer) < 64:
                    self.telnet_sb_buffer += byte
                else:
                    self.telnet_got_sb = False
                    self.telnet_sb_buffer = ""
            else:
                ## Just a normal NVT character
                return False

        ## Byte handling when already in an IAC sequence sent from the DE
        else:
            ## Did we get sent a second IAC?
            if byte == IAC and self.telnet_got_sb == True:
                ## Must be an escaped 255 (IAC + IAC)
                self.telnet_sb_buffer += byte
                self.telnet_got_iac = False

            ## Do we already have an IAC + CMD?
            elif self.telnet_got_cmd:
                ## Yes, so handle the option
                self._three_byte_cmd(byte)

            ## We have IAC but no CMD
            else: ## Is this the middle byte of a three-byte command?                
                if byte == DO:
                    self.telnet_got_cmd = DO
                elif byte == DONT:
                    self.telnet_got_cmd = DONT
                elif byte == WILL:
                    self.telnet_got_cmd = WILL
                elif byte == WONT:
                    self.telnet_got_cmd = WONT
                else: ## Nope, must be a two-byte command
                    self._two_byte_cmd(byte)

        # logger.debug("Telnet negotiation character %d", ord(byte))
                    
        self.negotiationByteCount += 1
        return True

    def _two_byte_cmd(self, cmd):

        """
        Handle incoming Telnet commands that are two bytes long.
        """

        #print "got two byte cmd %d" % ord(cmd)

        if cmd == SB:
            ## Begin capturing a sub-negotiation string
            self.telnet_got_sb = True
            self.telnet_sb_buffer = ''

        elif cmd == SE:
            ## Stop capturing a sub-negotiation string
            self.telnet_got_sb = False
            self._sb_decoder()

        elif cmd == NOP:
            pass

        elif cmd == DATMK:
            pass

        elif cmd == IP:
            pass

        elif cmd == AO:
            pass

        elif cmd == AYT:
            pass

        elif cmd == EC:
            pass

        elif cmd == EL:
            pass

        elif cmd == GA:
            pass

        else:
            logger.debug("%s: Should not be here", "2BC")

        self.telnet_got_iac = False
        self.telnet_got_cmd = None

    def _three_byte_cmd(self, option):
        """
        Handle incoming Telnet commmands that are three bytes long.
        """

        ## Incoming DO's and DONT's refer to the status of this end
        cmd = self.telnet_got_cmd
        # print "got three byte cmd %d:%d" % (ord(cmd), ord(option))
        cb = { ECHO: self.echo_cb, COMPRESS2: self.compress2_cb }.get(option, None)

        if cmd == DO:
            if option in (COMPRESS2, ECHO, SGA):
                if self._check_reply_pending(option):
                    self._note_reply_pending(option, False)
                    self._note_local_option(option, True)
                    cb and cb(True)
                elif (self._check_local_option(option) == False or self._check_local_option(option) == UNKNOWN):
                    self._note_local_option(option, True)
                    self._iac_will(option)
                    cb and cb(True)
            else:
                ## ALL OTHER OTHERS = Default to refusing once
                if self._check_local_option(option) == UNKNOWN:
                    self._note_local_option(option, False)
                    self._iac_wont(option)
        elif cmd == DONT:
            if option in (BINARY, ECHO, COMPRESS2):            
                if self._check_reply_pending(option):
                    self._note_reply_pending(option, False)
                    self._note_local_option(option, False)
                    cb and cb(False)                        
                elif (self._check_local_option(BINARY) == True or self._check_local_option(BINARY) == UNKNOWN):
                    self._note_local_option(option, False)
                    self._iac_wont(option)                    
                    cb and cb(False)                        
            elif option == SGA:
                if self._check_reply_pending(SGA):
                    self._note_reply_pending(SGA, False)
                    self._note_local_option(SGA, False)
                elif (self._check_remote_option(SGA) == True or self._check_remote_option(SGA) == UNKNOWN):
                    self._note_local_option(SGA, False)
                    self._iac_will(SGA) # WHY WILL HERE?
                    ## Just nod
            else:
                ## ALL OTHER OPTIONS = Default to ignoring
                pass

        ## Incoming WILL's and WONT's refer to the status of the DE
        elif cmd == WILL:
            if option in (ECHO, COMPRESS2): ## Decline.
                ## Nutjob DE offering to echo or compress the server...
                if self._check_remote_option(option) == UNKNOWN:
                    self._note_remote_option(option, False)
                    # No no, bad DE!
                    self._iac_dont(option)
            elif option in (NAWS, SGA): ## Accept.
                if self._check_reply_pending(option):
                    self._note_reply_pending(option, False)
                    self._note_remote_option(option, True)
                    ## NAWS: Nothing else to do, client follow with SB

                elif (self._check_remote_option(option) == False or
                        self._check_remote_option(option) == UNKNOWN):
                    self._note_remote_option(option, True)
                    self._iac_do(option)
                    ## NAWS: Client should respond with SB
            elif option == TTYPE:
                # Putty sends this unbidden.    
                if self._check_reply_pending(option):
                    self._note_reply_pending(option, False)
                self._note_remote_option(option, True)

                ## TTYPE: Tell them to send their terminal type
                if self.send_cb:
                    self.send_cb('%c%c%c%c%c%c' % (IAC, SB, TTYPE, SEND, IAC, SE))

        elif cmd == WONT:
            if option in (ECHO, COMPRESS2):
                ## DE states it wont echo or compress2 us -- good, they're not suppose to.
                if self._check_remote_option(option) == UNKNOWN:
                    self._note_remote_option(option, False)
                    self._iac_dont(option)
            elif option in (SGA, TTYPE):
                if self._check_reply_pending(option):
                    self._note_reply_pending(option, False)
                    self._note_remote_option(option, False)
                elif (self._check_remote_option(option) == True or self._check_remote_option(option) == UNKNOWN):
                    self._note_remote_option(option, False)
                    self._iac_dont(option)
        else:
            logger.debug("%s: Should not be here", "3BC")

        self.telnet_got_iac = False
        self.telnet_got_cmd = None

    def _sb_decoder(self):
        """
        Figures out what to do with a received sub-negotiation block.
        """

        bloc = self.telnet_sb_buffer
        if len(bloc) > 2:
            if bloc[0] == TTYPE and bloc[1] == IS:
                # Basically each one we are informed of is a selection.  So we
                # need to select each offered one to identify the range, and then
                # reselect until we have our preferred one selected.
            
                terminal_type = bloc[2:].lower()
                if self.desired_terminal_type is None:
                    # Select terminal types until we have covered all the options.
                    if terminal_type not in self.terminal_types:
                        self.terminal_types.append(terminal_type)
                        # Ask for the next terminal type.
                        self.send_cb('%c%c%c%c%c%c' % (IAC, SB, TTYPE, SEND, IAC, SE))
                    else:
                        # Ask the application which terminal type to use.
                        self.desired_terminal_type = self.terminal_type_selection_cb(self.terminal_types)
                        if self.desired_terminal_type == terminal_type:
                            # Bingo.  The preferred terminal type has been selected.
                            if self.terminal_type_cb:
                                self.terminal_type_cb(terminal_type)
                        else:
                            # Start the terminal type selection process again.
                            self.request_terminal_type()
                elif terminal_type != self.desired_terminal_type:
                    # If the current terminal type is not the preferred one, ask for the next.
                    self.send_cb('%c%c%c%c%c%c' % (IAC, SB, TTYPE, SEND, IAC, SE))
                else:
                    # Bingo.  The preferred terminal type has been selected.
                    if self.terminal_type_cb:
                        self.terminal_type_cb(terminal_type)

            elif bloc[0] == NAWS:
                if len(bloc) != 5:
                    logger.debug("Bad length on NAWS SB: %d", len(bloc))
                elif self.terminal_size_cb:
                    rows = (256 * ord(bloc[3])) + ord(bloc[4])
                    columns = (256 * ord(bloc[1])) + ord(bloc[2])
                    self.terminal_size_cb(rows, columns)

                #print "Screen is %d x %d" % (self.columns, self.rows)

        self.telnet_sb_buffer = ''

    #---[ State Juggling for Telnet Options ]----------------------------------

    ## Sometimes verbiage is tricky.  I use 'note' rather than 'set' here
    ## because (to me) set infers something happened.

    def _check_local_option(self, option):
        """Test the status of local negotiated Telnet options."""
        if not self.telnet_opt_dict.has_key(option):
            self.telnet_opt_dict[option] = TelnetOption()
        return self.telnet_opt_dict[option].local_option

    def _note_local_option(self, option, state):
        """Record the status of local negotiated Telnet options."""
        if not self.telnet_opt_dict.has_key(option):
            self.telnet_opt_dict[option] = TelnetOption()
        self.telnet_opt_dict[option].local_option = state

    def _check_remote_option(self, option):
        """Test the status of remote negotiated Telnet options."""
        if not self.telnet_opt_dict.has_key(option):
            self.telnet_opt_dict[option] = TelnetOption()
        return self.telnet_opt_dict[option].remote_option

    def _note_remote_option(self, option, state):
        """Record the status of local negotiated Telnet options."""
        if not self.telnet_opt_dict.has_key(option):
            self.telnet_opt_dict[option] = TelnetOption()
        self.telnet_opt_dict[option].remote_option = state

    def _check_reply_pending(self, option):
        """Test the status of requested Telnet options."""
        if not self.telnet_opt_dict.has_key(option):
            self.telnet_opt_dict[option] = TelnetOption()
        return self.telnet_opt_dict[option].reply_pending

    def _note_reply_pending(self, option, state):
        """Record the status of requested Telnet options."""
        if not self.telnet_opt_dict.has_key(option):
            self.telnet_opt_dict[option] = TelnetOption()
        self.telnet_opt_dict[option].reply_pending = state


    #---[ Telnet Command Shortcuts ]-------------------------------------------

    def _iac_do(self, option):
        """Send a Telnet IAC "DO" sequence."""
        if self.send_cb:
            self.send_cb('%c%c%c' % (IAC, DO, option))

    def _iac_dont(self, option):
        """Send a Telnet IAC "DONT" sequence."""
        if self.send_cb:
            self.send_cb('%c%c%c' % (IAC, DONT, option))

    def _iac_will(self, option):
        """Send a Telnet IAC "WILL" sequence."""
        if self.send_cb:
            self.send_cb('%c%c%c' % (IAC, WILL, option))

    def _iac_wont(self, option):
        """Send a Telnet IAC "WONT" sequence."""
        if self.send_cb:
            self.send_cb('%c%c%c' % (IAC, WONT, option))
