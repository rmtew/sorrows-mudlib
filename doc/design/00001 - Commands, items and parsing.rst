%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
 Commands, items and parsing
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

Like most areas of development, it is easy to get bogged down in the
possibilities.  To aim for the most interesting implementation that can be
conceived, delaying work on it until the design is fully fleshed out.  So,
the goal of this document is to lay out the plan for the implementation of
item handling related commands.

Milestone: The room
-------------------

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

Parsing
^^^^^^^

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

Displaying
^^^^^^^^^^

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

Use Case
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

Working Notes
^^^^^^^^^^^^^
A lot of the work involved in this, has been rewriting existing code, or moving code that is sandbox game specific under that game directory.  In fact, maintaining the sandbox code has become impractical and at some later point it needs to be revisited and reconciled with the mudlib and the simple room game.

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

Milestone: Containers and plurals
---------------------------------

This is composed of four commands:

* put <subject> in <object>
* take <subject> from <object>
* look <object>
* open <object>
* close <object>

In addition, it includes the extension of objects and the parser to specifying and using plurals.

This milestone is not very detailed because at face value, the work involved seems straightforward.

Plurals
^^^^^^^

What are the repercussions of plurals on the parser?  Currently I match objects based on the noun used, but this does not take into the plural form.  If someone says "take swords", then this means that it should be attempted to take all the swords they can reach.  And if someone says "take sword", then this means that they should take one sword.

What if the plural form is the same as the singular form?  If the parser knows whether the match was to the use of a plural, or a singular noun, then it might act on it.  But how it should act in this ambiguous case is unclear.  Perhaps players should be required to use determiners (all, every, ..) to indicate that an action relates to multiple items.

Now looking at adjectives which are determiners.  "take every sword".  "take all swords".  Hmm, "all" requires a plural, and if someone is taking swords, then they are already implicitly taking all of them.  So "every" is the form which I would need to handle.  A quick Google says that this type of adjective are called distributive determiners.

Reading about types of determiners brings some other ideas up, like part of the scope of handling plurals might be selection, like how many of the matches to take.  Let's say there are five nuts and the player only needs two, they might do "take two nuts".

As I have no idea how to resolve the problems mentioned above, I am going to choose a simplistic solution for now.  Nouns are going to be interpreted as meaning one item, regardless of whether they are singular or plural.  To shift the intepretation to more than one item, will require the player provide a distributive determiner adjective.  If a numeric qualifier is specified, then it overrides the determiner.

Parsing
^^^^^^^

I need to add storage of plurals to objects and I need to have the parser check against those plurals when I am doing the parsing.  Now the simple approach would be to require the content creator to specify the plural form of any singular noun they used.  But if this can be done automatically on their behalf, then not to do it adds an unnecessary burden on the user.

Potential code::

  class Object:
      def __init__(self):
          self.nouns = set()
          self.plurals = set()

      def AddNoun(self, noun):
          noun = noun.strip().lower()
          self.nouns.add(noun)
          plural = textsupport.Pluralise(noun)
          self.plurals.add(plural)

      def AddPlural(self, plural):
          self.plurals.add(plural.strip().lower())

The grammatical rules for pluralisation are documented on various web sites.

Potential code::

  def Pluralise(noun):
      plural = {
          "bison": "bison",
          "goose": "geese",  # Irregular nouns
          "moose": "moose",
          "mouse": "mice",
          "ox":    "oxen",
          "sheep": "sheep",
          "foot":  "feet",
          "tooth": "teeth",
          "man":   "men",
          "woman": "women",
          "child": "children",
      }.get(noun, None)
      if plural is not None:
          return plural
  
      sEnding = noun[-2:]
      pEnding = {
          "ss": "sses",   # bus      -> busses
          "zz": "zzes",   # ?
          "sh": "shes",   # bush     -> bushes
          "ch": "ches",   # branch   -> branches
          "fe": "ves",	  # knife    -> knives
          "ff": "ffs",	  # cliff    -> cliffs

          "ay": "ays",	  # <vowel>y -> <vowel>ys
          "ey": "eys",	  # 
          "iy": "iys",	  # 
          "oy": "oys",	  # 
          "uy": "uys",	  # 
      }.get(sEnding, None)
      if pEnding is not None:
          return noun[:-2] + pEnding

      sEnding = noun[-1]
      pEnding = {
          "y": "ies",     # family   -> families
          "f": "ves",     # loaf     -> loaves
      }.get(sEnding, None)
      if pEnding is not None:
          return noun[:-1] + pEnding

      pEnding = {
          "s": "",        # pants    -> pants
          "x": "es",      # fox      -> foxes
      }.get(sEnding, None)
      if pEnding is not None:
          return noun + pEnding

      # Fallback case.
      logger.error("Failed to pluralise '%s'", noun)
      return noun +"s"
      
  Pluralize = Pluralise   # American <- English

Descriptions
^^^^^^^^^^^^

How should a container describe that it contains multiple similar objects?  The straightforward approach is simply to list them all.

  "You see: An old sword, a new sword, a long sword, a broadsword and a short sword."

What if similar objects were when displayed in passing, described in a collective form.

  "You see: A variety of swords."

.. note::

    I think this is definitely worth exploring at a later point, but it is getting into the realm of fancy extras that overcomplicate things at this early state.

Use Case
^^^^^^^^

As it stands from milestone 1, the starting room has a pair of brown pants in it.  In order to handle the testing of containers, and the use of commands to interact with them, a container is needed.  In this case, the container will be a chest.  In order to bring into play the plural parser behaviour, there needs to be multiple objects present with the same noun.  This will be an additional pair of pants, although green rather than brown, to differentiate them.

Working Notes
^^^^^^^^^^^^^

With most of the mudlib cleanup work having been done in the previous milestone, this one was relatively straightforward.

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
* Extended the object class to track plurals, using the new 'pluralise' function.
* Added two functions to the object class to help the parser to match it, 'IdentifiedBy' which takes a noun and indicates whether it relates to the given object either as in the singular or plural forms, and 'DescribedBy' which takes a set of adjectives and indicates whether the given object is described by all of them.  These are now used for matching, rather than direct use of an objects 'nouns' and 'adjectives' attributes.
* If the "all" or "every" adjectives are used, the parser notes that the desired amount of matches are effectively as many as have been found, as noted in the design otherwise this is one desired match.
* If the parser finds multiple matches and the number of matches found is higher than the desired amount of matches, then the user is asked which of the matches they want.
* Objects can now have names.  If the name of the object is the same as its short, the plural form of the noun is not automatically generated and added.  This is to handle cases where short descriptions are actually names, like the player's name for instance.
* 'take <object>' and 'drop <object>' have implied locations which the given object resides in.  For 'drop' this is in the player's inventory.  For 'take' this is in the room.  To remove ambiguity, two new syntax tokens have been added, both forms of 'SUBJECT'.  'SUBJECTR' indicates an object that is located in the room.  'SUBJECTB' indicates an object that is located in the player.

Further work
^^^^^^^^^^^^
* Object names. These were added to differentiate between names of objects and descriptions of objects.  Is this really needed?
* The new parser syntax tokens 'SUBJECTR' and 'SUBJECTB'.  These address the problem they were meant to solve, but the use of an extra letter to indicate context is not the clearest of solutions.  It might be worth creating longer more explicit tokens to use at a later stage, or.. something.
* Parser match objects and the event system. The matched objects found by the parser, are collected in a 'Match' class which is a subclass of 'list'.  The automatic dispatching of events hashes instances of classes, and it turns out that instances of classes like 'list' are not hashable, so the event system chokes on instantiation of these classes.  For now, the event system ignores subclasses like these, but that is not the correct solution.
* Parser failure messages.  At the moment the parser failure messages are simple, but they could be clearer and more useful.  For instance, rather than saying 'Which <object>?" as a failure message when multiple matches are found, it might say "Which <object>?  There are two <common description> here."
* Parser success messages.  Most of the success messages for commands so far, are ones that the parser could easily generate in much the same way as it supplies the chosen failure message.  That is, rather than having the command generate them.  Also, the messages should use short descriptions that are not just the noun, for instance with the correct article provided.  The parser would have to have some sort of feedback from the commands that indicated what objects the command operated on successfully, and which it did not.
* Safe object movement.  At the moment there is no protection against race conditions when actions are performed on multiple objects.  For instance, most of the game commands iterate over the matched objects.  If some of the objects the iteration has not yet reached have in the meantime been moved (perhaps taken by another player) then the iteration will proceed to operate on them regardless.

Milestone: An acceptable level of polish
----------------------------------------

This milestone was inserted to get work done that is more important than the milestones that follow.  The previous milestones have introduced a basic set of desired functionality and while the goal is not to overcomplicate things, a certain level of polish is needed for that basic set to be considered finished and usable.

* Articles [#farticles]_ not added to the short description of objects.  If it is, then the text in which those descriptions appear, would appear more natural and less out of place.
* Parser failure messages are simple.  But it is important that enough information is given that the user can work out why the given message appeared.  Each parser message should be improved if improvement is possible.
* Success messages are dumb.  For each object that a command is applied to, a separate message is displayed.  It is entirely possible to collect the objects operated on, and to display a composite message.

Articles
^^^^^^^^

No article applies to when the short description is a name.  "the" applies when there is only one of an item.  "a" / "an" apply when there are more than one items and only one is being used.

Hypothetical usage::

  There are five swords.
  > take one sword
  You take a sword.
  
  There is a sword.
  > take sword
  You take the sword.

  You see: Five swords, an apple, Pete and a dog.

So, "the" applies to specific items.  And "a" or "an" apply to any items.

Failure messages
^^^^^^^^^^^^^^^^

At this time, there are two failure messages used by the parser:

* "You cannot find any STRING.": Used when looking for an object that matches STRING, but unable to find any.
* "Which STRING?": Used when looking for an object that matches STRING, but more than one are found when only one is wanted.

First considering "You cannot find any STRING."  A first thought is that STRING could be broken down and the noun extracted, and the pluralised form of that noun used in place of STRING in this message.  So where STRING is "any red sword", the correct displayable form of STRING might be "swords".  "You cannot find any swords."  Actually, that would be confusing if there were swords, just no red ones.  So the distributive adjectives might be stripped, and the attributive ones like "red" kept.  "You cannot find any red swords."  Another variant might be "There are no red swords here."  If "here" is to be interpreted as the room, then if the expected location of the item is carried by the actor, alternately something more specific like "You are not carrying a red sword."  It might be worth experimenting with how varying the message depending on context works in practice.

Next considering "Which STRING?"  In this case we have matches, just too many.  We would want to use the attributive adjectives with the noun.  "take red sword" -> "Which red sword?"  Or "There are two red swords, which one do you want to take?"

It is all very well to write about these things here, but doing so shows that the concepts need to be tried out.  One way which would demonstrate the range of cases that need to be supported and show how they work, would be to write unit tests for the parser.  In fact, that seems to be the most obvious lesson that this exploration of concepts shows.

Unit tests::

    class ParserTests(unittest.TestCase):
        pass

Success messages
^^^^^^^^^^^^^^^^

One of the entries in the future work of the last milestone, was to look at moving success messages from a given command into the parser to be handled generally.  To do this while making a composite success messages, would probably be worthwhile.  Otherwise, each command is going to have to add a lot of boilerplate and custom handling.

In order for the parser to be able to display success or failure messages, depending on how the syntax handler is able to work on the matched objects, 

This means the syntax handler that the parser calls needs to give it suitable feedback such that the parser can display success or failure, and the reasons why.  The pl

Use Case
^^^^^^^^

In the previous milestones, the use cases were aimed at providing a minimal scenario on which the functionality being implemented could be tested.  What I am wondering now, is whether a more extensive scenario would be useful.  Not going for broke and fleshing out a game world, but rather a minimal game world that would allow a better insight into how well the existing functionality works.  In fact, not only does it makes sense for better looking at the existing functionality, but it would give a better environment for inspiring ideas for future functionality.

Milestone: Character item exchange
----------------------------------

Character item exchange.

* give <item> to <living>
* take <item> to <living>
* demand <item> from <living>
* request <item> from <living>
* offer <item> to <living>

Working Notes
^^^^^^^^^^^^^

* I now consider this milestone to be outside the scope of this design.  It should be moved into another design.

Milestone: Declared nuances
---------------------------

Declared nuances.

* offer <item> to <living> unwillingly

Working Notes
^^^^^^^^^^^^^

* I now consider this milestone to be outside the scope of this design.  It should be moved into another design.

Footnotes
---------

.. [#farticles] http://owl.english.purdue.edu/owl/resource/540/01/
