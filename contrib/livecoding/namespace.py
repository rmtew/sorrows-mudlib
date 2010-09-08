# TODO:
# - DestroyNamespace may be a little enthusiastic.  Should check the contents
#   of a namespace which is presumed to be clean, before deleting it.  If there
#   is something left, then do the appropriate thing.
# - The namespace contributions can only come from one ScriptDirectory.
#   - __file__ might be made shorter and clearer by using paths relative to
#     the base directory.

import os
import sys
import imp
import traceback
import types
import logging
import unittest

logger = logging.getLogger("namespace")
#logger.setLevel(logging.DEBUG)

class ScriptFile(object):
    lastError = None
    namespaceContributions = None

    def __init__(self, filePath, namespacePath, implicitLoad=True, delGlobals=False):
        self.filePath = filePath
        self.namespacePath = namespacePath

        self.scriptGlobals = {}
        self.delGlobals = delGlobals

        if implicitLoad:
            self.Load(filePath)

    def __del__(self):
        if self.delGlobals:
            self.scriptGlobals.clear()
        # print "GC", self.namespacePath, self.filePath, hex(id(self.scriptGlobals))

    def __repr__(self):
        return "<ScriptFile filePath='%s' namespacePath='%s'>" % (self.filePath, self.namespacePath)

    def Load(self, filePath):
        self.filePath = filePath

        script = open(self.filePath, 'rU').read() +"\n"
        self.codeObject = compile(script, self.filePath, "exec")

    def GetAttributeValue(self, attributeName):
        return self.scriptGlobals[attributeName]

    def SetNamespaceContributions(self, namespaceContributions):
        self.namespaceContributions = namespaceContributions

    def AddNamespaceContributions(self, namespaceContributions):
        self.namespaceContributions |= namespaceContributions
        
    def Run(self):
        self.scriptGlobals = {}

        try:
            eval(self.codeObject, self.scriptGlobals, self.scriptGlobals)
        except (ImportError, AttributeError):
            # Likely reasons for encountered errors:
            #  ImportError: A namespace has not been exported yet.
            #  AttributeError: A namespace attribute is not exported yet.
            self.lastError = traceback.format_exception(*sys.exc_info())
            return False

        return True

    def UnitTest(self):    
        dirPath, scriptFileName = os.path.split(self.filePath)
        testScriptPath = os.path.join(dirPath, scriptFileName[:-3] + "_unittest.py")
        testFileExists = os.path.exists(testScriptPath)

        # Create a throwaway script file object for the unit test script.
        scriptFile = self.__class__(testScriptPath, None, implicitLoad=testFileExists)
        if testFileExists:
            scriptFile.Run()

        # Inject the main script file contents underneath the test script contents.
        scriptFile.scriptGlobals.update(self.scriptGlobals)

        # Gather all the unit tests from any test suites.
        testSuite = unittest.TestSuite()
        for testCase in scriptFile.scriptGlobals.values():
            if type(testCase) is types.TypeType or type(testCase) is types.ClassType:
                if issubclass(testCase, unittest.TestCase):
                    subSuite = unittest.defaultTestLoader.loadTestsFromTestCase(testCase)
                    testSuite.addTests(subSuite)

        logger.debug("UnitTest extracted %d tests", testSuite.countTestCases())

        testResult = unittest.TestResult()
        testSuite.run(testResult)

        if testResult.errors or testResult.failures:
            self.lastError = []
        
            lastTestCase = None
            for errorTestCase, tracebackText in testResult.errors:
                if lastTestCase is not errorTestCase:
                    self.lastError.append("Error in test case '%s'" % errorTestCase.__class__.__name__)
                    lastTestCase = errorTestCase
                self.lastError.append(tracebackText)

            lastTestCase = None
            for failureTestCase, tracebackText in testResult.failures:
                if lastTestCase is not failureTestCase:
                    self.lastError.append("Failure in test case '%s'" % failureTestCase.__class__.__name__)
                    lastTestCase = failureTestCase
                self.lastError.append(tracebackText)

            return False

        # No unit tests, or the unit tests did not error or fail.
        return True

    def LogLastError(self, flush=True, context="Unknown logic"):
        if self.lastError is None:
            logger.error("Script file '%s' unexpectedly missing a last error", self.filePath)
            return

        logger.error("Error executing script file '%s'\n%s", self.filePath, "".join(self.lastError).rstrip("\r\n"))

        if flush:
            self.lastError = None

    def GetExportableAttributes(self):
        import __builtin__, types
        # No point handing around standard global objects.
        # Is this line in particular needed?
        builtinValues = set(__builtin__.__dict__.itervalues())
        # Some objects in types are special __builtin__ sourced ones.
        builtinValues.update(v for k, v in types.__dict__.iteritems() if k[0] != '_')

        for k, v in self.scriptGlobals.iteritems():
            if k == "__builtins__":
                continue

            valueType = type(v)
            exportable = True
            # Modules will have been imported from elsewhere.
            if isinstance(v, types.ModuleType):
                exportable = False
            elif valueType in (types.ClassType, types.TypeType):
                # Classes with valid modules will have been imported from elsewhere.
                if v.__module__ != "__builtin__":
                    exportable = False
                # Skip actual builtin objects.
                elif v in builtinValues or issubclass(v, unittest.TestCase):
                    exportable = False

            yield k, v, valueType, exportable


class ScriptDirectory(object):
    scriptFileClass = ScriptFile

    unitTest = True
    dependencyResolutionPasses = 10

    def __init__(self, baseDirPath=None, baseNamespace=None, delScriptGlobals=False):
        # Script file objects indexed in different ways.
        self.filesByPath = {}
        self.filesByDirectory = {}

        # Personal references to created namespaces.
        self.namespaces = {}

        self.classCreationCallback = None
        self.validateScriptCallback = None
        self.delScriptGlobals = delScriptGlobals

        self.SetBaseDirectory(baseDirPath)
        self.SetBaseNamespaceName(baseNamespace)

    def __del__(self):
        self.Unload()

    def SetClassCreationCallback(self, ob):
        self.classCreationCallback = ob

    def SetValidateScriptCallback(self, ob):
        self.validateScriptCallback = ob        

    def SetBaseDirectory(self, baseDirPath):
        self.baseDirPath = baseDirPath

    def SetBaseNamespaceName(self, baseNamespaceName):
        self.baseNamespaceName = baseNamespaceName

    def GetNamespacePath(self, dirPath):
        namespace = self.baseNamespaceName
        relativeDirPath = os.path.relpath(dirPath, self.baseDirPath)
        if relativeDirPath != ".":
            namespace += "."+ relativeDirPath.replace(os.path.sep, ".")
        return namespace

    def Load(self):
        ## Pass 1: Load all the valid scripts under the given directory.
        self.LoadDirectory(self.baseDirPath)
        
        ## Pass 2: Execute the scripts, ordering for dependencies and then add the namespace entries.
        scriptFilesToLoad = set(self.filesByPath.itervalues())
        attemptsLeft = self.dependencyResolutionPasses
        while len(scriptFilesToLoad) and attemptsLeft > 0:
            logger.debug("ScriptDirectory.Load dependency resolution attempts left %d", attemptsLeft)

            if len(scriptFilesToLoad) == 1:
                attemptsLeft = 1

            scriptFilesLoaded = set()
            for scriptFile in scriptFilesToLoad:
                if self.RunScript(scriptFile):
                    scriptFilesLoaded.add(scriptFile)

            # Update the set of scripts which have yet to be loaded.
            scriptFilesToLoad -= scriptFilesLoaded

            attemptsLeft -= 1

        if len(scriptFilesToLoad):
            logger.error("ScriptDirectory.Load failed to resolve dependencies")

            # Log information about the problematic script files.
            for scriptFile in scriptFilesToLoad:
                scriptFile.LogLastError()

            return False

        return True

    def LoadDirectory(self, dirPath):
        logger.debug("LoadDirectory %s", dirPath)

        namespace = self.GetNamespacePath(dirPath)

        for entryName in os.listdir(dirPath):
            if entryName == ".svn":
                continue

            entryPath = os.path.join(dirPath, entryName)
            if os.path.isdir(entryPath):
                self.LoadDirectory(entryPath)
            elif os.path.isfile(entryPath):
                if not entryName.endswith(".py") or entryName.endswith("_unittest.py"):
                    continue

                scriptFile = self.LoadScript(entryPath, namespace)
                self.RegisterScript(scriptFile)
            else:
                logger.error("Unrecognised type of directory entry %s", entryPath)

    def Unload(self):
        if not len(self.filesByPath) and not len(self.namespaces):
            return

        logger.debug("Cleaning up after removed directory '%s'", self.baseDirPath)

        for k, scriptFile in self.filesByPath.items():
            self.UnloadScript(scriptFile)
            del self.filesByPath[k]

        namespacePaths = self.namespaces.keys()
        namespacePaths.sort()
        namespacePaths.reverse()
        
        for namespacePath in namespacePaths:
            self.DestroyNamespace(namespacePath)

    def GetNamespace(self, namespaceName):
        return self.namespaces[namespaceName]

    def CreateNamespace(self, namespaceName, filePath):
        module = self.namespaces.get(namespaceName, None)
        if module is not None:
            if filePath in module.__file__:
                raise RuntimeError("Namespace already exists", namespaceName)
            return module

        if namespaceName in sys.modules:
            raise RuntimeError("Namespace already occupied", namespaceName)

        parts = namespaceName.rsplit(".", 1)
        if len(parts) == 2:
            baseNamespaceName, moduleName = parts
            baseNamespace = self.CreateNamespace(baseNamespaceName, filePath)
        else:
            baseNamespaceName, moduleName = None, parts[0]
            baseNamespace = None

        logger.info("Creating namespace '%s'", namespaceName)

        module = imp.new_module(namespaceName)
        # module.__name__ = moduleName
        # Our modules don't map to files.  Have a placeholder.
        module.__file__ = ""
        module.__package__ = baseNamespaceName

        self.namespaces[namespaceName] = module
        sys.modules[namespaceName] = module

        if baseNamespace is not None:
            setattr(baseNamespace, moduleName, module)

        return module

    def DestroyNamespace(self, namespaceName):
        module = self.namespaces.get(namespaceName, None)
        if module.__file__:
            logger.debug("DestroyNamespace '%s' skipping, still used %s", namespaceName, module.__file__)
            return

        logger.debug("DestroyNamespace '%s'", namespaceName)
        del sys.modules[namespaceName]
        del self.namespaces[namespaceName]

    def RegisterScript(self, scriptFile):
        # Index the file by its full path.
        self.filesByPath[scriptFile.filePath] = scriptFile

        dirPath = os.path.dirname(scriptFile.filePath)
        relativeDirPath = os.path.relpath(dirPath, self.baseDirPath)

        # Index the file with other files in the same directory.
        if relativeDirPath not in self.filesByDirectory:
            self.filesByDirectory[relativeDirPath] = []
        self.filesByDirectory[relativeDirPath].append(scriptFile)

    def UnregisterScript(self, scriptFile):
        dirPath = os.path.dirname(scriptFile.filePath)
        relativeDirPath = os.path.relpath(dirPath, self.baseDirPath)

        self.filesByDirectory[relativeDirPath].remove(scriptFile)
        if not len(self.filesByDirectory[relativeDirPath]):
            del self.filesByDirectory[relativeDirPath]

        del self.filesByPath[scriptFile.filePath]

    def FindScript(self, filePath):
        if filePath in self.filesByPath:
            return self.filesByPath[filePath]

    def LoadScript(self, filePath, namespacePath):
        logger.debug("LoadScript %s", filePath)

        return self.scriptFileClass(filePath, namespacePath, delGlobals=self.delScriptGlobals)

    def RunScript(self, scriptFile, tentative=False):
        logger.debug("RunScript %s", scriptFile.filePath)

        if not scriptFile.Run():
            logger.debug("RunScript failed")
            return False

        # Give whatever is using the framework to analyse and reject script changes.
        if not self.BroadcastValidateScriptEvent(scriptFile):
            return False

        if self.unitTest and not scriptFile.UnitTest():
            logger.debug("RunScript tests failed or errored")
            return False

        if not tentative:
            logger.debug("RunScript exporting to namespace %s", scriptFile.namespacePath)

            namespace = self.CreateNamespace(scriptFile.namespacePath, scriptFile.filePath)
            self.SetModuleAttributes(scriptFile, namespace)

        return True

    def BroadcastValidateScriptEvent(self, scriptFile):
        if self.validateScriptCallback:
            try:
                if type(self.validateScriptCallback) is tuple:
                    getattr(self.validateScriptCallback[0], self.validateScriptCallback[1])(scriptFile)
                else:
                    self.validateScriptCallback(scriptFile)
            except ReferenceError:
                self.validateScriptCallback = None
            except Exception:
                scriptFile.lastError = traceback.format_exception(*sys.exc_info())
                return False
        return True

    def UnloadScript(self, scriptFile, force=False):
        namespace = self.GetNamespace(scriptFile.namespacePath)
        if self.RemoveModuleAttributes(scriptFile, namespace):
            return True
        return False            

    def SetModuleAttributes(self, scriptFile, namespace, overwritableAttributes=set()):
        moduleName = namespace.__name__
        
        # Track what files have contributed to the namespace.
        if scriptFile.filePath not in namespace.__file__:
            if len(namespace.__file__):
                namespace.__file__ += ";"
            namespace.__file__ += scriptFile.filePath

        namespaceContributions = set()
        for k, v, valueType, exportable in scriptFile.GetExportableAttributes():
            logger.debug("InsertModuleAttribute %s.%s exported=%s", moduleName, k, exportable)

            if not exportable:
                logger.debug("Added a non-exported global: %s %s", k, valueType)
                continue

            # By default we never overwrite.  This way we can identify duplicate contributions.
            if hasattr(namespace, k) and k not in overwritableAttributes and k != "__doc__":
                logger.error("Duplicate namespace contribution for '%s.%s' from '%s', our class = %s", moduleName, k, scriptFile.filePath, v.__file__ == scriptFile.filePath)
                continue

            if valueType in (types.ClassType, types.TypeType):
                v.__module__ = moduleName
                v.__file__ = scriptFile.filePath

            setattr(namespace, k, v)

            namespaceContributions.add(k)

            if type(v) in (types.TypeType, types.ClassType):
                self.BroadcastClassCreationEvent(v)
            # print namespace, k, type(v)

        scriptFile.SetNamespaceContributions(namespaceContributions)

    def BroadcastClassCreationEvent(self, *args):
        if self.classCreationCallback:
            try:
                if type(self.classCreationCallback) is tuple:
                    getattr(self.classCreationCallback[0], self.classCreationCallback[1])(*args)
                else:
                    self.classCreationCallback(*args)
            except ReferenceError:
                self.classCreationCallback = None
            except Exception:
                logger.exception("Error broadcasting class creation")

    def RemoveModuleAttributes(self, scriptFile, namespace):
        logger.debug("RemoveModuleAttributes %s", scriptFile.filePath)
        if scriptFile.namespaceContributions is None:
            return True

        paths = namespace.__file__.split(";")
        if scriptFile.filePath not in paths:
            raise RuntimeError("Namespace mismatch")
        paths.remove(scriptFile.filePath)
        namespace.__file__ = ";".join(paths)

        for k in scriptFile.namespaceContributions:
            delattr(namespace, k)

        return True

