# Event broadcast and subscription

import unittest, traceback
import uthread

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
                traceback.print_exc()

    def ProcessClass(self, klass):
        # TODO: If we modify a class, then we are possibly interfering with the
        # code reloading.  It is best if the hooks mentioned below are put in
        # place by the code reloading system itself.

        eventMatches = ProcessClass(instance.__class__)

        # Is the class already processed?
        #   If there are no matches, then expunge it.
        # If there are matches, then:
        #   Inject some hooks in the class to add newly created instances as listeners.

        for eventName, functionName in eventMatches:
            pass

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
    def testEventFunctionDetection(self):
        class OneEvent:
            def __init__(self): pass        
            def event_SomeEvent(self): pass
            def AnotherFunction(self): pass

        l = ProcessClass(OneEvent)
        self.failUnless(len(l) == 1, "Did not find just one event function")
        eventName, functionName = l[0]
        self.failUnless(eventName == "SomeEvent", "Extracted incorrect event name")
        self.failUnless(functionName == "event_SomeEvent", "Extracted incorrect function name")

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
