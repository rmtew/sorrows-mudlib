"""
Module: events.py
Author: Richard Tew <richard.m.tew@gmail.com>

This module supports three different event subscription scenarios.

1. Manual registration of object instances.

  eh.Register(instance)

2. Manual registration of direct callbacks.

  eh.ServicesStarted.Register(function)

3. Automatic registration of object instances.

  This usage requires use of a code reloading system.  The following
  pseudo-code illustrates how this might work.  The onus is on the
  user to do the required integration.

  Custom data storage:
  
    __EVENTS__ = set([ "SomeEvent" ])
    
      This attribute would be placed by this process, as a record of
      what events instances of the class are registered for.

  Pseudo-code:

      def OnClassChanged(class, instances):
          oldEvents = getattr(class, "__EVENTS__", set())
      
          matches = eh.ProcessClass(class)
          if len(matches):
              ## Handle instances yet to be created.
              old_init = class.__init__
              def new_init(self, *args, **kwargs):
                  eh.Register(self)
                  old_init(*args, **kwargs)
              class.__init__ = new_init
          
              ## Handle existing instances.
              newEvents = set([ t[0] for t in matches ])
              
              # Remove existing registrations.
              removedEvents = oldEvents - newEvents
              addedEvents = newEvents - oldEvents
              matchesLookup = dict(matches)
              for instance in instances:
                  for eventName in removedEvents:
                      eh._Unregister(eventName, instance)
                  for eventName in addedEvents:
                      eh._Register(eventName, instance, matchesLookup[eventName])

              class.__EVENTS__ = newEvents

"""

import unittest, traceback, types, weakref, logging
import uthread

logger = logging.getLogger("events")

## BROADCASTING

# EVENTS

class Event(object):
    def __init__(self, handler, eventName):
        self.handler = handler
        self.eventName = eventName
        self.state = -1

    def __call__(self, *args, **kwargs):
        self.Broadcast(*args, **kwargs)
        return self

    def Broadcast(self, *args, **kwargs):
        self.state = 0
        try:
            self.handler.__Broadcast(self.eventName, *args, **kwargs)
        finally:
            self.state = 1

    def Register(self, callback):
        return self.handler.__Register(self.eventName, callback)

    @property
    def delayed(self):
        return self.state == -1

    @property
    def delivering(self):
        return self.state == 0

    @property
    def delivered(self):
        return self.state == 1


class BlockingEvent(Event):
    pass

class NonBlockingEvent(Event):
    def __call__(self, *args, **kwargs):
        uthread.new(self.Broadcast, *args, **kwargs)
        return self

# EVENT HANDLER:

class NonBlockingEventHandlerProxy:
    def __init__(self, handler):
        self.handler = handler

    def __getattr__(self, attrName):
        if attrName.startswith("__") or attrName in self.__dict__:
            return object.__getattr__(self, attrName)

        return NonBlockingEvent(self.handler, attrName)

class EventHandler(object):
    def __init__(self):
        self.registry = {}

    @property
    def launch(self):
        """ Returns a non-blocking event handler. """
        return NonBlockingEventHandlerProxy(self)

    def __getattr__(self, attrName):
        """ Returns an object representing the event with the given name. """
        if attrName in self.__dict__ or attrName.startswith("__"):
            return object.__getattr__(self, attrName)
    
        return BlockingEvent(self, attrName)

    def _Event__Broadcast(self, eventName, *args, **kwargs):
        """ A request by an event to do a broadcast on its behalf. """
        subscribers = self.registry.get(eventName, {})
        for subscriber, functionName in subscribers.iteritems():
            function = getattr(subscriber, functionName)
            try:
                function(*args, **kwargs)
            except Exception:
                logger.exception("Error broadcasting '%s' to a subscriber", eventName)

    def _Event__Register(self, eventName, function):
        """ A request by an event to register for an event on its behalf. """
        if type(function) is not types.MethodType:
            return False

        self._Register(eventName, function.im_self, function.func_name)
        
        return True

    def _Register(self, eventName, instance, functionName):
        registry = self.registry.get(eventName, None)
        if registry is None:
            registry = self.registry[eventName] = weakref.WeakKeyDictionary()
        registry[instance] = functionName

    def _Unregister(self, eventName, instance):
        registry = self.registry.get(eventName, None)
        if instance in registry:
            del registry[instance]

    def Register(self, instance):
        """ Allow an instance to be registered for events it declares an interest in. """
        for eventName, functionName in ProcessClass(instance.__class__):
            self._Register(eventName, instance, functionName)


## SUBSCRIPTION

def ProcessClass(klass):
    return [
        (k[6:], k)
        for k
        in klass.__dict__
        if k.startswith("event_")
    ]

## UNIT TESTS

class SubscriptionTests(unittest.TestCase):
    def setUp(self):
        class OneEvent:
            def __init__(self): pass        
            def event_SomeEvent(self): pass
            def AnotherFunction(self): pass

        self.klass = OneEvent
        self.eh = EventHandler()

    def testEventFunctionDetection(self):
        l = ProcessClass(self.klass)
        self.failUnless(len(l) == 1, "Did not find just one event function")
        eventName, functionName = l[0]
        self.failUnless(eventName == "SomeEvent", "Extracted incorrect event name")
        self.failUnless(functionName == "event_SomeEvent", "Extracted incorrect function name")

    def testManualInstanceRegistration(self):
        instance = self.klass()
        
        self.eh.Register(instance)
        
        def event_SomeEvent(*args, **kwargs):
            self.failUnless(args == (1, 2), "Did not receive positional arguments")
            self.failUnless(kwargs == { "kw": "yes" }, "Did not receive keyword arguments")

        instance.event_SomeEvent = event_SomeEvent
        self.eh.SomeEvent(1, 2, kw="yes")

    def testManualFunctionRegistration(self):
        class Test:
            def callback(testSelf, *args, **kwargs):
                self.failUnless(args == (1, 2), "Did not receive positional arguments")
                self.failUnless(kwargs == { "kw": "yes" }, "Did not receive keyword arguments")

        instance = Test()
        self.eh.SomeEvent.Register(instance.callback)
        self.eh.SomeEvent(1, 2, kw="yes")

class BroadcastTests(unittest.TestCase):
    def setUp(self):
        self.event = EventHandler()

        self.uthread_new = uthread.new
        uthread.new = lambda *args, **kwargs: None

    def tearDown(self):
        uthread.new = self.uthread_new

    def testBlockingEventCreation(self):
        event = self.event.ServicesStarted()
        self.failUnless(isinstance(event, BlockingEvent), "Event was not blocking by default")
        self.failUnless(event.delivered, "Event did not complete its broadcast before returning")

    def testNonBlockingEventCreation(self):
        event = self.event.launch.ServicesStarted()
        self.failUnless(isinstance(event, NonBlockingEvent), "Event was not non-blocking by default")
        self.failUnless(event.delayed, "Event did not delay its broadcast")


if __name__ == "__main__":    
    unittest.main()
