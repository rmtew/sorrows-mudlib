%%%%%%%%%%%%%%%%%%%%%%%%%%%
 Inventory and Encumbrance
%%%%%%%%%%%%%%%%%%%%%%%%%%%

.. ======================================================================== ..

Milestone: Encumbrance
----------------------

This doesn't really add that much at this point, so probably best not to spend
too much time on it.

Points to address
^^^^^^^^^^^^^^^^^

1. How to tell how much an item weighs.
2. How to tell how much an character can carry.
3. What happens when carries weight approaches or passes the limit.

Use Case
^^^^^^^^

How the above points are to be handled, would determine the use case.

Working Notes
^^^^^^^^^^^^^

* Implemented object weight.
* Implemented body max carried weight.
* Incomplete WRT 3.

.. ======================================================================== ..

Milestone: Inventory
--------------------

At the simplest level, this adds slots where objects can be placed.

Points to address
^^^^^^^^^^^^^^^^^

1. What are the default slots?
2. Do they differ per-race?
3. How would a backpack add carrying capacity?

Brainstorm
^^^^^^^^^^

Default slots might be:
* Head.  Wear one item (headwear).
* Torso.  Wear one item (torso).
* Left hand.  Wear one item (glove).  Hold one item (hand).
* Right hand.  Wear one item (glove).  Hold one item (hand).
* Feet.  Hold one item (footwear).
* Legs.  Hold one item (legs).

Special cases which came up:
* Back should be an additional wear slot.
  * Shield can be worn on the back when not in use.
  * Pack can be worn on the back.
  * Bow can be worn on the back when not in use.
* Accessories / jewelery.
  * Slots:
    * neck (jewellery / accessories).
    * eyes (glasses / blindfold).
    * waist (belt / scabbard).
    * ankle (manacle).
    * wrist (manacle).

Items / Item properties
^^^^^^^^^^^^^^^^^^^^^^^

Start with just brainstorming and then move onto formalising it as a system
I can put in game.

Brainstorming
`````````````

Just a brain dump of ideas and slots.

::

    Fitting slot types:
    * Headwear.
    * Torso.
    * Hand.
    * Legs.
    * Feet.
    * Back.
    * Waist.

    Shield:
    * Wear: back.
    * Use: hand.

    Scabbard:
    * Wear: waist / back.

    Sword:
    * Wear: scabbard.
    * Use: hand.

    Quiver:
    * Wear: back.

    Arrow:
    * Wear: quiver.

    Spear:
    * Wear: back.
    * Use: hand.

    Pack:
    * Wear: back.

    Sack

    Longbow:
    * Wear: back.
    * Use: hand.

Formalising
```````````

The above is a good breakdown of interested information.  But it would be best
to have it specified in a data driven way.  And the last thing I want to do is
write my own custom parsing format, or for that matter use something heavy-
weight like YAML or XML.  Even JSON looks cumbersome.  Perhaps INI..

::

    [inventory]
    slot-types=wear, use
    wear-slots=head, torso, left-hand, right-hand, waist, legs, feet, back
    use-slots=left-hand, right-hand
    hold-slots=left-hand, right-hand

    [inventory-property-types]
    slot-types=strings
    wear-slots=strings
    use-slots=strings

    [item-property-types]
    name=string
    weight=float
    use-slots=strings
    wear-slots=strings

    [container-property-types]
    capacity=float

    [class-hierarchy]
    container=item

    [item-sword]
    name=sword
    weight=1.0
    wear-slots=scabbard

    [container-scabbard]
    name=scabbard
    weight=1.0
    capacity=0.0

    wear-slots=back, waist

    [container-quiver]
    name=quiver
    weight=0.2
    wear-slots=back

    [item-arrow]
    name=arrow
    weight=0.05
    use-slots=quiver

    [item-shield]
    name=shield
    weight=3.0
    use-slots=left-hand, right-hand
    wear-slots=back

    [container-pack]
    name=pack
    weight=0.1
    wear-slots=back

    [container-sack]
    name=sack
    weight=0.1

    [item-spear]
    name=spear
    weight=0.5
    wear-slots=back
    use-slots=left-hand, right-hand

    [item-longbow]
    name=longbow
    weight=2.0
    wear-slots=back
    use-slots=left-hand, right-hand

That's a good initial set of data.  At a later point, I'd like to have the
data source be the D20 open data.  But regardless of where the data comes from
I need administration commands to query.

::

    > data list items
    A           B           C           D           E           F
    G           H           I           J           K           L
    > data list containers
    A           B           C
    > data make A

That takes me to the point I have a range of items, and can instantiate them
on demand.  Then I should be able to use them appropriately, whether holding
or wearing.

::

    > wear shield
    ...
    > hold shield
    ...
    > wear quiver on back
    ...
    > wear scabbard on belt
    ...

XXX
