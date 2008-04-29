# Want a base object which will only provide calls I want it to provide and
# only accept the arguments I want and then return the result I want.

from __future__ import with_statement
import os, weakref, types
import __builtin__

class Object(object):
    pass

class MonkeyPatcher(object):
    def __init__(self):
        self.dirTree = {}
        self.store = {}

    def __enter__(self):
        for k, v in MonkeyPatcher.__dict__.iteritems():
            if not k.startswith("MP_"):
                continue

            # Store the original value.
            self.store[v.__doc__] = eval(v.__doc__)

            # Insert our replacement value.
            idx = v.__doc__.rfind(".")
            moduleName, attrName = v.__doc__[:idx], v.__doc__[idx+1:]
            setattr(eval(moduleName), attrName, getattr(self, k))

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for k, v in self.store.iteritems():
            # Restore the original value.
            idx = k.rfind(".")
            moduleName, attrName = k[:idx], k[idx+1:]
            setattr(eval(moduleName), attrName, v)

        return False

    # ...

    def SetDirectoryStructure(self, dirTree):
        self.dirTree = dirTree

    def GetDirectoryEntry(self, path):
        v = self.dirTree
        bits = path.split(os.path.sep)
        for bit in bits:
            if not v.has_key(bit):
                e = IOError(2, "No such file or directory")
                e.filename = path
                raise e
            v = v[bit]
        return v

    def SetFileContents(self, path, contents):
        dirPath, fileName = os.path.split(path)
        v = self.GetDirectoryEntry(dirPath)
        v[fileName] = contents

    def RemoveDirectoryEntry(self, path):
        d = self.dirTree
        dirPath, fileName = os.path.split(path)
        dirBits = dirPath.split(os.path.sep)

        for bit in dirBits:
            d = d[bit]

        del d[fileName]

    # Monkeypatched functions.

    def MP_os_listdir(self, path):
        "os.listdir"
        v = self.GetDirectoryEntry(path)
        if type(v) is dict:
            return v.keys()
        elif type(v) is list:
            return v

    def MP_os_path_isfile(self, path):
        "os.path.isfile"
        v = self.GetDirectoryEntry(path)
        return type(v) in types.StringTypes

    def MP_os_path_isdir(self, path):
        "os.path.isdir"
        v = self.GetDirectoryEntry(path)
        return type(v) == types.DictType

    def MP_os_path_exists(self, path):
        "os.path.exists"
        try:
            self.GetDirectoryEntry(path)
            return True
        except IOError:
            return False

    def MP_open(self, path):
        "__builtin__.open"
        v = self.GetDirectoryEntry(path)

        instance = Object()
        instance.read = lambda: v
        instance.close = lambda: None
        return instance

if __name__ == "__main__":
    d = {
        "A": {
            "a.py": "#...",
        },
        "B": {
            "b.py": "#...",
        },
    }

    aFileName = os.path.join("A", "a.py")

    with MonkeyPatcher() as mp:
        mp.SetDirectoryStructure(d)

        # print os.listdir("A")

        mp.SetFileContents(aFileName, "#....")
