%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
 00001 - Commands, items and parsing
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

Design
======

Like most areas of development, it is easy to get bogged down in the
possibilities.  To aim for the most interesting implementation that can be
conceived, delaying work on it until the design is fully fleshed out.  So,
the goal of this document is to lay out the plan for the implementation of
item handling related commands.

Milestones:

#. Interaction with the room.
#. Interaction with containers and use of plurals.
#. Interaction with other characters.
#. Declared nuances.

Milestone 1: The room
---------------------

This is composed of two commands:

* take <object>
* drop <object>

It is the most basic level of item iteraction.  And it drives the
implementation of other functionality it relies on.

Command Syntax
^^^^^^^^^^^^^^

I loosely envision that a command should have the possible syntax that it can
be used with specified as strings.

A theoretical definition::

  class TakeCommand(WorldCommand):
      __verbs__ = [ "take" ]
      __syntax__ = [
          "OBJECT",
      ]
  
So when the "take" command is executed, the parser will look at the selection
of different syntax that can be used for it.  Then it will try and reconcile
the arguments provided to the command with that syntax.

Thinking through an example, a given command might be "take the brown pants".
Now as the only syntax available is "OBJECT", the parser will try and
reconcile "the brown pants" with any object that is within reach of the
player.  In an ideal world, this would be in any container the player might
possess (a backpack they are wearing), any container the player might be
able to reach or access (a closed locked chest on the ground that they have
the key to) or so on.  But I am aiming for the simplest case I can handle, so
that I actually get something implemented.  So in the real world, this would
resolve to items they are carrying in their hands, and items that are on the
ground.

What the take command knows that the parser does not, is that it will be
moving objects into the player's hands.  Therefore it will subsequently
filter out the objects that are already in the player's hands, and those that
remain in the parsers list, are candidates for movement.

Objects and Parsing
^^^^^^^^^^^^^^^^^^^

The parser will narrow down the list of relevant items.  It will take into
account any adjectives that the actor provides in their command.  The pants
in the example command above are qualified with the adjective "brown".

So having gathered all the items that the player has in their hands and all
the items that are on the ground, the parser will check the noun "pants"
against the nouns that describe those objects.  And for each object that has
the noun "pants", its adjectives will be checked for the word "brown".  The
resulting list will be passed to the executing command.

An open question is what to do about the word "the".  The use of it implies
that there is only one pair of brown pants present.  And "pants" is both the
singular and plural form of "pants", so the parser should really display a
failure message to the user if more than one pair of matching pants are
reachable.  But for now, perhaps it is best to just identify and discard
articles like "the".

An idea came to mind while writing the possible parser code.  Currently the
event system detects registrations based on the presence of methods with the
naming prefix of 'event\_'.  It would be equally possible to declare handled
syntax in the same way by function name in WorldCommand subclasses.

Possible parser code::

  class Parser:
      def Parse(self, string, user):
          idx = words.find(" ")
          if idx == -1:
              verb = words[:idx]
              string = []
          else:
              verb = words[:idx]
              string = string[idx:].strip()

          access = user.__access__
          commandClass = sorrows.commands.GetCommandClass(verb, access)
          command = commandClass(user.shell)
          
          if not issubclass(commandClass, WorldCommand):
              try:
                  return command.Run(verb, argString)
              finally:
                  command.Release()
          
          # Code that does the parsing resolution matching stuff.

The world command initialisation would examine the methods on the class of
the current command.  Similarly named methods in base classes are considered
irrelevant for this.  It would identify methods that declare themselves as
handlers of given syntaxes.

Possible WorldCommand code::

  class WorldCommand(Whatever):  
      def __init__(self):
          self.__syntax__ = []

          for attrName in self.__class__.__dict__:
              if attrName.startswith("syntax_"):
                  self.__syntax__.append(attrName[7:])

A syntax handling method in a world command would receive a representation
of the entity that us referred to in the character's command.  Now the
parser will have narrowed down the possible matching entities based on the
adjectives and noun used, but this may leave a range of possible matches.
I was going to say that it is up to the method to deal with the matches,
but that is not true.  If there are two "brown pants" matched, then the
parser could tell the character this.  The player might then reference the
"second brown pants", allowing the parser to isolate a match.

But then the character might reference in the plural form, intending that
they take all the "brown pants" present.  So the parser must always give the
method lists as values to address that one or more valid matches may be made.

Possible WorldCommand subclass code::

  class TakeCommand(WorldCommand):
      def syntax_SUBJECT(self, subjects):
          pass

      def syntax_SUBJECT_from_OBJECT(self, subjects, objects):
          pass

Of course I am trying to avoid thinking about "pants".  As a noun it is a
valid way to refer to one pair of pants, or more than one pair of pants.
This adds a new question.  For similar nouns, should all of the items be
taken, or should it be up to the character to specify that more than one
should be taken.  "take all brown pants from chest"  So now we have another
need from objects, that they be referable by the plural forms of their nouns.

Now I am wondering about the question of constraints.  The parser enforces
the visibility constraints.  I was going to say reachability, but there will
be cases where the player wants to refer to items that they cannot reach.
Perhaps "cast beacon on robert's broach".  Although Robert's broach is
visible, it might also be grabbed, so therefore it is still reachable.  I
don't know.  I'll stick with reachable for now.

But anyway.. constraints.  The parser provides objects that the character is
capable of performing the action with, based on their description.  It does
not know about any other constraints that might prevent the action from
succeeding on those objects.  The command will have to explicitly handle these
things for now.  Whether the character can take the broach Robert is wearing,
for instance.  Whether something exists to prevent the character from casting
a spell on Robert's person, or perhaps even the broach itself.

These syntax handling methods remind me of the MudOS parser.  It might be a
good idea to go back (after this is implemented) and see what inspiration can
be drawn from it.

Objects and Displaying
^^^^^^^^^^^^^^^^^^^^^^

Traditionally, objects have two types of descriptions.  The 'short'
description that is used to represent it in passing, whether in a room
description, or perhaps describing it in use within a larger sentence.
And the 'long' description that is used to describe it.  You might look
in a room, see the sword is there, then look at it directly to find out
more about it.

None of this is currently implemented.  But this is a good basic outline,
and I should as noted in the parser section, collect the nouns and verbs
for reference.

Possible code::

  class Object:
      primaryNoun = None
      shortDescription = None
      longDescription = ""

      def __init__(self, shortDescription=None):
          self.nouns = set()
          self.adjectives = set()

          if shortDescription is not None:
	      self.SetShortDescription(shortDescription)

      def AddNoun(self, noun):
          self.nouns.add(noun.strip().lower())

      def AddAdjective(self, adjective):
          self.adjectives.add(adjective.strip().lower())

      def SetShortDescription(self, shortDescription):
          self.shortDescription = shortDescription

          words = self.shortDescription.lower().split(" ")

          # The last word is the noun.
          self.primaryNoun = words.pop().strip()
          self.nouns.add(self.primaryNoun)

          for word in words:
              self.adjectives.add(word.strip())

      def GetShortDescription(self):
          return self.shortDescription

      def SetLongDescription(self, longDescription):
          self.longDescription = longDescription

      def GetLongDescription(self):
          return self.longDescription

Now this is a good start.  The nouns and adjectives are isolated in a form
that the parser can refer to and work with, once it has gathered the reachable
objects.  But one requirement I have not addressed is how the description
presented to the "look" command is generated.  On one hand, there is an
inkling that I might put it in Object.  But on the other, any future need can
put it in the best place, and for now simply building it into the "look"
command is a good start.

Rooms
^^^^^

Rooms contain things, as do for that matter characters.  So I need to add
newly created characters to a starting room.  If the Room object derives from
Object, then it gains short and long descriptions which it needs.  For now,
I will leave off rooms being attached to other rooms, where characters can
move between them, although that is an easy extension.

When a character is removed from the game, as part of the cleanup, they should
be removed from the room they are in.  Logging in to see older versions of
yourself is a good symptom of this problem.

Possible code::

  class Room(Object):
      pass

For the "take" command:  The parser should look for an object in the room the
character is in, and present it to the command, passed into the syntax
handling method that applies.  The syntax handling method should implement
logic that checks that the object can be taken, that the character has room
for the object and then moves the object from the room into the character.

For the "drop" command:  The parser should look for an object in the character
and present it to the command.  The syntax handling method should check that
the object can be moved into the room, check that the object can be moved out
of the character and then move the object from the character into the room.

Now there is a question about how the parser should work.  For both "get" and
"drop", it is know where the subject should be found.  But naively returning
matching objects that are within the set of reachable ones, the parser is
doing more work than it should.  That the parser should only look for the
subject in the character, or in the room, is not something that can be
encoded in the syntax handling method name.  So to keep things simple and not
get side-tracked, should the onus be on the method to ignore objects from
the wrong container?  For lack of a better idea, this will have to be the way
it will work.

Scenario
^^^^^^^^

Up to this point, the scope of what has been defined is how rooms, objects and
the parser work together within the limited extent to which they have been
explored.  A good addition to these abstract elements, is a scenario in which
they are employed.

Staging the scenario:

#. Create a room.
#. Have the login process place the player in that room.
#. Add an object to the room.

Okay, I am going to keep this really simple.  The object is going to be a pair
of pants.

Milestone 2: Containers and plurals
-----------------------------------

This is composed of four commands:

* put <subject> in <object>
* take <subject> from <object>
* look <object>
* open <object>
* close <object>

In addition, it includes the extension of objects and the parser to specifying and using plurals.

This milestone is not very detailed because at face value, the work involved seems straightforward.

Scenario
^^^^^^^^

Taking the scenario from milestone 1 and adding a container to it, and also adding another object with the same noun, should do it.

So, adding a chest, and a pair of differently coloured pants.

Milestone 3: Character item exchange
------------------------------------

Character item exchange.

* give <item> to <living>
* take <item> to <living>
* demand <item> from <living>
* request <item> from <living>
* offer <item> to <living>

Milestone 4: Declared nuances
-----------------------------

Declared nuances.

* offer <item> to <living> unwillingly

Working Notes
=============

Milestone 1: The room
---------------------

A lot of the work involved in this, has been rewriting existing code, or moving code that is sandbox game specific under that game directory.  In fact, maintaining the sandbox code has become impractical and at some later point it needs to be revisited and reconciled with the mudlib and the simple room game.

Notes
^^^^^

* Many the existing game-related commands derived from WorldCommand.  This was a legacy of the sandbox, where the world was switchable through the 'world' command.  As this is no longer relevant to the mudlib, or the simple room game, it has been moved into the sandbox directory,
* Created a new subclass of PlayerCommand called GameCommand.  The goal is that no game command defines a Run method to handle the command execution, instead it defines the syntax handlers described in the design for this milestone.  Ideally defining a Run method on subclasses of GameCommand should be prevented.
* GameCommand.Run calls the new parser service.
* Extended the livecoding framework to allow a callback to be set, where the callback gives the encompassing framework a chance to analyse and reject changed scripts.  This is now used to reject subclasses of GameCommand that define a Run method.
* Each of the Command subclasses (not BaseCommand) defines a required access mask.
* Refactored the Command service to index commands by their access mask (e.g. COMMAND_GAME), which is better than the indexing under labels (e.g. "developer") which it had before.  It can also have aliases defined for each command (e.g. "n" -> "north").
* The simple room game world service now creates a starting room and moves newly logged in bodies there.  It contains a pants object.  A new inheritance hierarchy of Room -> Container -> Object and Body -> Container -> Object facilitates this.
* Added an Object.MoveTo function that is used to move objects into a container.  It takes care of removing them from any container they are already located within before adding them into the next one.  The container of an object is stored on the object as a weakref.
* The parser service was extended to handle the one argument case, where the argument was either an object (take sword) or a string (say something).
* All the existing game-related commands that can be are moved to GameCommand.  The exceptions are 'look' and 'move' which require the no argument case to work.
* The parser service was extended to handle the no argument case, and this meant that 'look' and 'move' could be converted over to use the GameCommand subclass.
* Aliases no longer appear in the list of commands shown in by the 'commands' command.

Further work
^^^^^^^^^^^^

* One argument syntaxes that match objects, have to look for those objects in all naturally reachable containers (the actor's body and the room).  Given that the command knows what locations should be searched and has to do the filtering anyway, this creates complexity.  There needs to be a way to specify scope for tokens in a command syntax, and given how well the function naming approach is working, it will most likely have to be special token names for this one argument case.
* The syntax handlers and the parser need work to allow them to handle use of plurals, and qualifiers like "all" and "every".  Maybe even "first", "second", etc.  This shows in the design decisions made, like in the case of multiple matches failing with a message asking "Which SUBJECT?" or whatever.  And in the implementation of syntax handlers where the code just dumps some helpless text at the user.
* Articles.  The short descriptions need to be qualified with the appropriate article for the context in which they feature.  I am not sure how to go about this for now, and am willing to leave it to a later stage.

Milestone 2: Containers and plurals
-----------------------------------

With most of the mudlib cleanup work having been done in the previous milestone, this one was relatively straightforward.

Notes
^^^^^

* Added an extra syntax to 'take' for '<subject> from <object>', and an extra syntax to 'put' for '<subject> in <object>'.  At this point they just display the matches for each token to the user.
* Extended the parser to handle the three argument case, with the requirement that the second argument is a preposition.  This allows the new 'take' and 'put' syntaxes to display the matches their usage results in.
* The parser is hitting the more simplistic syntaxes before the more complex ones, so 'take pants from chest' results in a failure message of "You can't find any pants from chest." as the '<subject>' syntax is hit rather than the '<subject> from <object>' syntax.  This is fixed by sorting the list of handled syntax for a given command into order of decreasing complexity, with number of tokens being most important, and use of the string token being least important.
* The parser is generating a failure message for the more complex syntax of "take <subject> from <object>"), when the least complex usage is actually tried ("take <subject>").  This is fixed by collecting failure messages for each syntax tried.  If a syntax is valid, then its handler is called and the failures are discarded.  Otherwise, the failure message for the most complex syntax is displayed.  This seems to work for now.
* The use of the preposition "from" implies where to look for the subject, and in this case the set of reachable objects is considered to be the matches for the object.
* There is a problem with the use of weakref for the reference to the container an object is in.  It means that comparisons like 'ob is context.room' fails, because 'ob' is a proxied weakref object.  Removed the use of weakref proxy objects for this purpose and just store a normal object reference now.
* The 'take' and 'put' commands now work for all desired syntaxes.
* Generation of the look description for the room a body was in, was on the body.  Now it has been moved to the room.  And it incorporates the look description of the container, which incorporates the look description of the object.  Each of these is generated by the object being described.
* Extended 'look' to handle the 'look <object>' case.  Through the look description generation process already established, it shows the object description and reflects the contents of the object if it is a container.
* The 'look' command now works for all desired syntaxes.

Further work
^^^^^^^^^^^^

* Consider the scenario where there are pants and a chest in the room.  The user enters "put pants in chest" and they see a message along the lines of "What pants?".  This is because the 'put' command filters out subject matches that are not located in the body.  Wouldn't the correct behaviour here be implicit actions, where the actor would try and perform a "take pants" first, then would proceed with their placement?

Milestone 3: Character item exchange
------------------------------------

TBD

Milestone 4: Declared nuances
-----------------------------

TBD