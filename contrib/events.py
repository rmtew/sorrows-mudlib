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
"""

import unittest, traceback, types, weakref, logging
import stackless

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
        stackless.tasklet(self.Broadcast)(*args, **kwargs)
        return self

# EVENT HANDLER:

class NonBlockingEventHandlerProxy:
    """
    Wrapper for 'events.launch.EventName()' behaviour
    """
    def __init__(self, handler):
        self.handler = handler

    def __getattr__(self, attrName):
        if attrName.startswith("__") or attrName in self.__dict__:
            return object.__getattr__(self, attrName)

        return NonBlockingEvent(self.handler, attrName)
    

class EventHandler(object):
    def __init__(self):
        self.registry = {}
        self.classRegistry = {}
        
        self.instances = weakref.WeakKeyDictionary()

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
        del self.registry[eventName][instance]

    def Register(self, instance):
        """ Allow an instance to be registered for events it declares an interest in. """

        if instance in self.instances:
            return

        self.instances[instance] = None

        # Collect the events the instance needs to be registered for..
        # TODO: Replace this with cached data.
        classes = [ instance.__class__ ]
        collectedEvents = set()
        while len(classes):
            class_ = classes.pop()            
            if class_ is types.ObjectType:
                continue

            collectedEvents |= class_.__events__            
            classes.extend(class_.__bases__)

        if len(collectedEvents):
            logger.debug("<%s[%x]> %s", instance.__class__, id(instance), list(collectedEvents))

        # Register the instance for the collected events.            
        for eventName in collectedEvents:
            functionName = "event_"+ eventName
            self._Register(eventName, instance, functionName)

    def ProcessClass(self, class_):
        """ Detect changes in the events this class infers instances of itself will
        be subscribed for. """

        # These cannot be hashed.  Just do not support events on them.
        if issubclass(class_, (dict, list, tuple, set)):
            return

        oldEvents = class_.__events__

        newEventData = dict(
            (k[6:], k)
            for k
            in class_.__dict__
            if k.startswith("event_")
        )
        newEvents = class_.__events__ = set(newEventData)

        self.MonitorClassInstantiation(class_)

        # Are there any changes to the events?  If not, then we need to do nothing.
        if oldEvents == newEvents:
            return

        # Cached state.
        
        subclassCache = {}
        def GetSubclasses(class_):
            if class_ not in subclassCache:
                subclassCache[class_] = class_.__subclasses__()
            return subclassCache[class_]            

        instanceCache = {}
        def GetInstances(class_):
            if class_ not in instanceCache:
                instanceCache[class_] = class_.__instances__()
            return instanceCache[class_]

        # For both addition and removal of handled events, we need to identify
        # the leaves the the inheritance tree that are affected by each of these.
        # Leaves are pruned where a subclass defines its own handler for an event.
        # Then the instances of the spliced tree are updated for the event change.

        # Unregister the class for events it no longer has listener methods for.
        unregisterTally = 0
        removedEvents = oldEvents - newEvents
        for eventName in removedEvents:
            # self.classRegistry[eventName].remove(class_)
            funcName = "event_"+ eventName

            # If there is a lower level handler for this event, it falls into
            # place to handle all instances above it which were affected by this
            # change.
            if hasattr(class_, funcName):
                continue

            # Unsubscribe all instances for this class and all relevant subclasses.
            subclasses = [ class_ ]
            while len(subclasses):
                subclass = subclasses.pop()
                
                # Does this subclass override the handling of this event?
                if eventName in subclass.__dict__["__events__"]:
                    continue

                # Unregister all instances of this subclass and continue up..
                for instance in GetInstances(subclass):
                    self._Unregister(eventName, instance)
                    unregisterTally += 1
                
                subclasses.extend(GetSubclasses(subclass))

        if len(removedEvents):
            logger.info("%s - %s (%d instances)", class_, list(removedEvents), unregisterTally)

        # Register the class for events it now has newly added listener methods for.
        registerTally = 0
        addedEvents = newEvents - oldEvents
        for eventName in addedEvents:
            # if eventName not in self.classRegistry:
            #     self.classRegistry[eventName] = []
            # self.classRegistry[eventName].append(class_)
            funcName = newEventData[eventName]

            # We only need to manage instances for this class, and its subclasses.
            # If the class inherits registration at a lower level, all instance subscriptions stand.
            handled = True            
            for baseClass in class_.__bases__:
                if hasattr(baseClass, funcName):
                    break
            else:
                handled = False

            if handled:
                continue

            # We need to register instances of this class, and its subclasses.    
            subclasses = [ class_ ]
            while len(subclasses):
                subclass = subclasses.pop()
                
                # Does this subclass override the handling of this event?
                if class_ is not subclass and eventName in subclass.__dict__["__events__"]:
                    continue

                # Unregister all instances of this subclass and continue up..
                for instance in GetInstances(subclass):
                    self._Register(eventName, instance, funcName)
                    registerTally += 1
                
                subclasses.extend(GetSubclasses(subclass))

        if len(addedEvents):
            logger.info("%s + %s (%d instances)", class_, list(addedEvents), registerTally)

    def MonitorClassInstantiation(self, class_):
        def init_wrapper(self, *args, **kwargs):
            class_.__real_init__(self, *args, **kwargs)
            events.Register(self)

        def init_standin(self, *args, **kwargs):
            if type(self) is types.InstanceType:
                for baseClass in class_.__bases__:
                    if hasattr(baseClass, "__init__"):
                        baseClass.__init__(self, *args, **kwargs)
            else:
                super(class_, self).__init__(*args, **kwargs)
            events.Register(self)

        ## Hook into the class, to get notified of the creation of instances.
        # This logic is invoked everytime the class is updated.  But for it to
        # work correctly, it needs to understand that if the class does not
        # define an __init__ method, our hook will still be in place.
        init_real = class_.__dict__.get("__init__", None)
        if init_real is None or init_real.func_name != "__init__":
            class_.__init__ = init_standin
            if init_real is not None and init_real.func_name == "init_wrapper":
                del class_.__dict__["__real_init__"]
        else:
            class_.__init__ = init_wrapper
            class_.__real_init__ = init_real

    # ---- consider whether to keep the following ----

    def FindClassListeners(self, class_, eventName):
        listeningClasses = self.FindClassListeners_(class_, eventName, "event_"+ eventName)

        instances = []
        for listeningClass in listeningClasses:
            instances.extend(listeningClass.__instances__())
        return instances

    def FindClassListeners_(self, class_, eventName, functionName):
        listeningClasses = [ class_ ]
        for subclass in class_.__subclasses__():
            if functionName not in subclass.__dict__:
                listeningClasses.extend(self.FindClassListeners_(subclass, eventName, functionName))
        return listeningClasses
            


## SUBSCRIPTION

def ProcessClass(klass):
    return [
        (k[6:], k)
        for k
        in klass.__dict__
        if k.startswith("event_")
    ]

## UNIT TESTS

try:
    import pysupport
    havePySupport = True
except ImportError:
    havePySupport = False

if havePySupport:
    class AutomaticSubscriptionTests(unittest.TestCase):
        def setUp(self):
            """        
                               A
                               |
                          .----+----. 
             listener --> B    C    D
                          |
                        .-+-.
                        E   F
                            |
                            G <-- listener
            """
            def instance_creation(instance):
                self.eh.Register(instance)

            def class_creation(class_):
                """
                - There are no instances of this class yet.
                """
                class_.__instances__ = classmethod(pysupport.FindClassInstances)
                if not hasattr(class_, "__subclasses__"):
                    class_.__subclasses__ = classmethod(pysupport.FindClassSubclasses)
                self.eh.ProcessClass(class_)


            def class_update(class_):
                pass

            self.events = []
            self.eh = EventHandler()

            # ....
            class A: pass

            class B(A):
                def event_Test(self_):
                    self.events.append(("B", self_))

            class C(A): pass

            class D(A): pass

            class E(B): pass

            class F(B): pass

            class G(F):
                def event_Test(self_):
                    self.events.append(("G", self_))

            # Collect the classes we have just defined.
            classesByName = {}
            keys = []
            for k, v in locals().iteritems():
                if type(v) in (types.TypeType, types.ClassType):
                    keys.append(k)
                    v.__events__ = set()

            keys.sort()

            for k in keys:
                v = locals()[k]
                class_creation(v)
                v.__init__ = instance_creation
                classesByName[v.__name__] = v

            # Make two instances of each.
            instancesByName = {}
            for class_ in classesByName.itervalues():
                l = instancesByName[class_.__name__] = []
                # for i in range(2):
                l.append(class_())

            self.classesByName = classesByName
            self.instancesByName = instancesByName

        def _sortedEvents(self):
            d = {}
            for k, v in self.events:
                if k in d:
                    d[k].append(v.__class__.__name__)
                else:
                    d[k] = [ v.__class__.__name__ ]
            for v in d.itervalues():
                v.sort()
            return d

        def testAStartsListening(self):
            """ Look at the inheritance tree shown in setUp.  Consider
            what the effect is if A defines a listener as well. """

            class_ = self.classesByName["A"]
            def f(self_):
                self.events.append(("A", self_))
            class_.event_Test = f
            self.eh.ProcessClass(class_)

            # Broadcast the Test event.
            self.eh.Test()        

            d = self._sortedEvents()
            self.failUnless(len(d) == 3, "event dict did not have the three expected keys, had: "+ str(d.keys()))
            self.failUnless("G" in d and d["G"] == [ "G" ], "G sourced event had unexpected listeners: "+ str(d["G"]))
            self.failUnless("B" in d and d["B"] == [ "B", "E", "F" ], "B sourced event had unexpected listeners: "+ str(d["B"]))
            self.failUnless("A" in d and d["A"] == [ "A", "C", "D" ], "A sourced event had unexpected listeners: "+ str(d["A"]))

        def testFStartsListening(self):
            """ Look at the inheritance tree shown in setUp.  Consider
            what the effect is if F defines a listener as well. """

            class_ = self.classesByName["F"]
            def f(self_):
                self.events.append(("F", self_))
            class_.event_Test = f
            self.eh.ProcessClass(class_)

            # Broadcast the Test event.
            self.eh.Test()

            d = self._sortedEvents()
            self.failUnless(len(d) == 3, "event dict did not have the three expected keys, had: "+ str(d.keys()))
            self.failUnless("G" in d and d["G"] == [ "G" ], "G sourced event had unexpected listeners: "+ str(d["G"]))
            self.failUnless("B" in d and d["B"] == [ "B", "E" ], "B sourced event had unexpected listeners: "+ str(d["B"]))
            self.failUnless("F" in d and d["F"] == [ "F", ], "F sourced event had unexpected listeners: "+ str(d["F"]))

        def testGStopsListening(self):
            """ Look at the inheritance tree shown in setUp.  Consider
            what the effect is if G removes its listener. """

            class_ = self.classesByName["G"]
            del class_.event_Test
            self.eh.ProcessClass(class_)

            # Broadcast the Test event.
            self.eh.Test()

            d = self._sortedEvents()
            self.failUnless(len(d) == 1, "event dict did not have the one expected keys, had: "+ str(d.keys()))
            self.failUnless("B" in d and d["B"] == [ "B", "E", "F", "G" ], "B sourced event had unexpected listeners: "+ str(d["B"]))

        def testBStopsListening(self):
            """ Look at the inheritance tree shown in setUp.  Consider
            what the effect is if B removes its listener. """

            class_ = self.classesByName["B"]
            del class_.event_Test
            self.eh.ProcessClass(class_)

            # Broadcast the Test event.
            self.eh.Test()

            d = self._sortedEvents()
            self.failUnless(len(d) == 1, "event dict did not have the one expected keys, had: "+ str(d.keys()))
            self.failUnless("G" in d and d["G"] == [ "G" ], "G sourced event had unexpected listeners: "+ str(d["G"]))


class SubscriptionTests(unittest.TestCase):
    def setUp(self):
        class OneEvent:
            __events__ = set()
            def __init__(self): pass        
            def event_SomeEvent(self): pass
            def AnotherFunction(self): pass

        class SubClass1(OneEvent):
            pass

        class SubClass2(SubClass1):
            def event_SomeEvent(self): pass

        self.klass = OneEvent
        self.subclass1 = SubClass1
        self.subclass2 = SubClass2
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
        
    def testFindClassListeners(self):
        # This test only applies if 'pysupport' is available.
        try:
            import pysupport
        except ImportError:
            return

        self.klass.__instances__ = classmethod(pysupport.FindClassInstances)
        self.klass.__subclasses__ = classmethod(pysupport.FindClassSubclasses)
    
        instance = self.klass()
        instance1_1 = self.subclass1()
        instance1_2 = self.subclass1()
        instances1 = set([ instance, instance1_1, instance1_2 ])
        instance2_1 = self.subclass2()
        instance2_2 = self.subclass2()
        instances2 = set([ instance2_1, instance2_2 ])

        instances = set(self.eh.FindClassListeners(self.klass, "SomeEvent"))
        self.failUnless(instances == instances1, "Failed to identify the valid listeners")
        instances = set(self.eh.FindClassListeners(self.subclass2, "SomeEvent"))
        self.failUnless(instances == instances2, "Failed to identify the valid listeners")


class BroadcastTests(unittest.TestCase):
    def setUp(self):
        self.event = EventHandler()

    def tearDown(self):
        pass

    def testBlockingEventCreation(self):
        event = self.event.ServicesStarted()
        self.failUnless(isinstance(event, BlockingEvent), "Event was not blocking by default")
        self.failUnless(event.delivered, "Event did not complete its broadcast before returning")

    def testNonBlockingEventCreation(self):
        event = self.event.launch.ServicesStarted()
        self.failUnless(isinstance(event, NonBlockingEvent), "Event was not non-blocking by default")
        self.failUnless(event.delayed, "Event did not delay its broadcast")

    def _testExceptionCatching(self):
        class TestClass:
            def event_SomeEvent(self):
                raise Exception, "LogTest"

        instance = TestClass()
        self.event.Register(instance)
        self.event.SomeEvent()


if __name__ == "__main__":    
    unittest.main()
