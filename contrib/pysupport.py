import gc, types, unittest, sys

def ReferringClass(v):
    matches = [
        v
        for v
        in gc.get_referrers(v)
        if type(v) is types.ClassType or type(v) is types.TypeType
    ]
    if len(matches) == 1:
        return matches[0]        

def FindSubclasses(class_, inclusive=False):
    subclasses = []
    if inclusive:
        subclasses.append(class_)

    for v in gc.get_referrers(class_):
        if type(v) is tuple and class_ in v:
            rclass_ = ReferringClass(v)
            subclasses.append(rclass_)
            if rclass_ is not None:
                subclasses.extend(FindSubclasses(rclass_))
    return subclasses

def FindInstances(class_):
    instances = {}
    for v in gc.get_referrers(class_):
        if type(v) is types.InstanceType and isinstance(v, class_):
            if class_ not in instances:
                instances[class_] = []
            instances[class_].append(v)
        elif type(v) is tuple and class_ in v:
            rclass_ = ReferringClass(v)
            if rclass_ is not None:
                instances.update(FindInstances(rclass_))
    return instances


def _SafeRepr(value):
    if type(value) is dict and "__builtins__" in value:
        oldEntry = value["__builtins__"]
        value["__builtins__"] = "BUILTIN-DICT-REMOVED"
        s = str(value)
        value["__builtins__"] = oldEntry
    else:
        s = str(value)
    return s

ListIteratorType = type(iter([]))
                    
def PrintReferrers(value, indent=2, seen=None, referrers=None, frames=None):
    if indent == 24:
        print (" " * indent) + "GAVE UP RECURSION AT", indent
        return

    # Initialise the recursively passes collections.  Can't do this in the
    # argument list, as those are instances used for all calls.
    if seen is None:
        seen = []
        referrers = []
        # Ignore the caller.
        frames = [ sys._getframe().f_back ]

    seen.append(value)
    frames.append(sys._getframe())

    ll = gc.get_referrers(value)
    print (" " * (indent-2)) + str(len(ll)), "REFERRERS FOR", type(value), _SafeRepr(value), hex(id(value)) 
    referrers.append(ll)

    for v in ll:
        if False and v is l:
            print (" " * indent) + "SKIPPED/is-outer-list", hex(id(v)), type(v)
            continue

        if v in referrers:
            print (" " * indent) + "SKIPPED/is-referrer-list", hex(id(v)), type(v)
            continue

        if v is seen:
            print (" " * indent) + "SKIPPED/is-seen-list", hex(id(v)), type(v)
            continue

        if v in seen:
            print (" " * indent) + "SKIPPED/seen", hex(id(v)), _SafeRepr(v)
            continue

        if type(v) is dict:
            if v.get("__name__", None) == "__builtin__":
                print (" " * indent) + "SKIPPED __builtins__", hex(id(v))
                continue
            # print (" " * indent) + "DICT", hex(id(v)), len(v), "entries", _SafeRepr(v)
        elif type(v) is types.FrameType:
            if v not in frames:
                print (" " * indent) + "FRAME", v
                import traceback
                traceback.print_stack(v)
            else:
                print (" " * indent) + "SKIPPED/is-local-frame", hex(id(v)), _SafeRepr(v)
            continue
        if type(v) in (list, dict, types.FunctionType, types.TypeType, types.ClassType, ListIteratorType, types.InstanceType, tuple):
            PrintReferrers(v, seen=seen, indent=indent+2, referrers=referrers, frames=frames)
        else:
            print (" " * indent) + "VALUE", type(v), v


## UNIT TESTS FOLLOW

class InstanceTests(unittest.TestCase):
    def setUp(self):
        class ClassOfInterest:
            pass

        class SomeOtherClass:
            pass

        class SingleInheritingClass(ClassOfInterest):
            pass

        class MultiInheritingClass(SomeOtherClass, ClassOfInterest):
            pass

        class IndirectClass(MultiInheritingClass):
            pass

        self.coi = ClassOfInterest()
        self.sic = SingleInheritingClass()
        self.soc = SomeOtherClass()
        self.mic = MultiInheritingClass()
        self.ic = IndirectClass()

    def testFindSubclasses(self):
        l = FindSubclasses(self.coi.__class__)
        self.failUnless(len(l) == 3, "Failed to locate the subclasses")
        self.failUnless(self.sic.__class__ in l, "SingleInheritingClass instance not found")
        self.failUnless(self.mic.__class__ in l, "MultiInheritingClass instance not found")
        self.failUnless(self.ic.__class__ in l, "IndirectClass instance not found")

    def testFindInstances(self):
        d = FindInstances(self.coi.__class__)
        self.failUnless(len(d) == 4, "Not enough entries")
        self.failUnless(self.coi.__class__ in d and len(d[self.coi.__class__]) == 1, "ClassOfInterest instance not found")
        self.failUnless(self.sic.__class__ in d and len(d[self.sic.__class__]) == 1, "SingleInheritingClass instance not found")
        self.failUnless(self.mic.__class__ in d and len(d[self.mic.__class__]) == 1, "MultiInheritingClass instance not found")
        self.failUnless(self.ic.__class__ in d and len(d[self.ic.__class__]) == 1, "IndirectClass instance not found")


if __name__ == "__main__":
    unittest.main()