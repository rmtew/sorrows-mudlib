import unittest
import os, sys, time, math
import inspect, copy
import logging

if __name__ == "__main__":
    currentPath = sys.path[0]
    parentPath = os.path.dirname(currentPath)
    if parentPath not in sys.path:
        sys.path.append(parentPath)

# Add test information to the logging output.    
class TestCase(unittest.TestCase):
    def run(self, *args, **kwargs):
        logging.debug("%s %s", self._testMethodName, (79 - len(self._testMethodName) - 1) *"-")
        super(TestCase, self).run(*args, **kwargs)


import namespace
import reloader

class ReloadableScriptDirectoryNoUnitTesting(reloader.ReloadableScriptDirectory):
    unitTest = False

class CodeReloadingTestCase(TestCase):
    def setUp(self):
        self.codeReloader = None
        
        scriptDirPath = GetScriptDirectory()
        scriptFilePath = os.path.join(scriptDirPath, "fileChange.py")

        if os.path.exists(scriptFilePath):
            os.remove(scriptFilePath)

    def tearDown(self):
        if self.codeReloader is not None:
            for dirPath in self.codeReloader.directoriesByPath.keys():
                self.codeReloader.RemoveDirectory(dirPath)

    def UpdateBaseClass(self, oldBaseClass, newBaseClass):
        import gc, types
        for ob1 in gc.get_referrers(oldBaseClass):
            # Class '__bases__' references are stored in a tuple.
            if type(ob1) is tuple:
                # We need the subclass which uses those base classes.
                for ob2 in gc.get_referrers(ob1):
                    if type(ob2) in (types.ClassType, types.TypeType):
                        if ob2.__bases__ is ob1:
                            __bases__ = list(ob2.__bases__)
                            idx = __bases__.index(oldBaseClass)
                            __bases__[idx] = newBaseClass
                            ob2.__bases__ = tuple(__bases__)

    def UpdateGlobalReferences(self, oldBaseClass, newBaseClass):
        """
        References to the old version of the class might be held in global dictionaries.
        - Do not worry about replacing references held in local dictionaries, as this
          is not possible.  Those references are held by the relevant frames.

        So, just replace all references held in dictionaries.  This will hit
        """
        import gc, types
        for ob1 in gc.get_referrers(oldBaseClass):
            if type(ob1) is dict:
                for k, v in ob1.items():
                    if v is oldBaseClass:
                        logging.debug("Setting '%s' to '%s' in %d", k, newBaseClass, id(ob1))
                        ob1[k] = newBaseClass


class CodeReloadingObstacleTests(CodeReloadingTestCase):
    """
    Obstacles to fully working code reloading are surmountable.
    
    This test case is intended to demonstrate how these obstacles occur and
    how they can be addressed.
    """

    def ReloadScriptFile(self, scriptDirectory, scriptDirPath, scriptFileName, mangleCallback=None):
        # Get a reference to the original script file object.
        scriptPath = os.path.join(scriptDirPath, scriptFileName)
        oldScriptFile = scriptDirectory.FindScript(scriptPath)
        self.failUnless(oldScriptFile is not None, "Failed to find the existing loaded script file version")
        self.failUnless(isinstance(oldScriptFile, reloader.ReloadableScriptFile), "Obtained non-reloadable script file object")

        # Replace and wrap the builtin.
        if mangleCallback:
            def intermediateOpen(openFileName, *args, **kwargs):
                # The flag needs to be in a place where we can modify it from here.
                replacedScriptFileContents[0] = True

                replacementFileName = mangleCallback(openFileName)
                logging.debug("Mangle file interception %s", openFileName)
                logging.debug("Mangle file substitution %s", replacementFileName)
                return oldOpenBuiltin(replacementFileName, *args, **kwargs)

            oldOpenBuiltin = __builtins__.open
            __builtins__.open = intermediateOpen
            try:
                replacedScriptFileContents = [ False ]
                result = self.codeReloader.ReloadScript(oldScriptFile)
            finally:
                __builtins__.open = oldOpenBuiltin

            # Verify that fake script contents were injected as requested.
            self.failUnless(replacedScriptFileContents[0] is True, "Failed to inject the replacement script file")
        else:
            result = self.codeReloader.ReloadScript(oldScriptFile)

        self.failUnless(result is True, "Failed to reload the script file")

        newScriptFile = scriptDirectory.FindScript(scriptPath)
        self.failUnless(newScriptFile is not None, "Failed to find the script file after a reload")

        if self.codeReloader.mode == reloader.MODE_OVERWRITE:
            self.failUnless(newScriptFile is not oldScriptFile, "The registered script file is still the old version")
        elif self.codeReloader.mode == reloader.MODE_UPDATE:
            self.failUnless(newScriptFile is oldScriptFile, "The registered script file is no longer the old version")
        
        return newScriptFile

    def testOverwriteDifferentFileBaseClassReload(self):
        """
        Reloading approach: Overwrite old objects on reload.
        Reloading scope: Different file.

        This test is intended to demonstrate the problems involved in reloading
        base classes with regard to existing subclasses.

        Problems:
        1) Class references used by subclasses, stored outside of the namespace.

           i.e. import module
                BaseClass = module.BaseClass

                class SubClass(BaseClass):
                    def __init__(self):
                        BaseClass.__init__(self)

           When 'module.BaseClass' is updated to a new version, 'BaseClass'
           will still refer to the old version.
           
           'SubClass' will also have the next problem.

        2) The class reference held by a subclass.

           i.e. SubClass.__bases__

           When 'module.BaseClass' is updated to a new version, 'SubClass.__bases__'
           will still hold a reference to the old version.

        """
        scriptDirPath = GetScriptDirectory()
        cr = self.codeReloader = reloader.CodeReloader()
        cr.scriptDirectoryClass = ReloadableScriptDirectoryNoUnitTesting

        scriptDirectory = cr.AddDirectory("game", scriptDirPath)
        self.failUnless(scriptDirectory is not None, "Script loading failure")

        import game

        oldStyleClass = game.OldStyleBase
        newStyleClass = game.NewStyleBase

        ## Obtain references and instances for the two classes defined in the script.
        oldStyleNamespaceClass = game.OldStyleSubclassViaNamespace
        oldStyleNamespaceClassInstance1 = oldStyleNamespaceClass()
        oldStyleGlobalReferenceClass = game.OldStyleSubclassViaGlobalReference
        oldStyleGlobalReferenceClassInstance1 = oldStyleGlobalReferenceClass()
        newStyleNamespaceClass = game.NewStyleSubclassViaNamespace
        newStyleNamespaceClassInstance1 = newStyleNamespaceClass()
        newStyleGlobalReferenceClass = game.NewStyleSubclassViaGlobalReference
        newStyleGlobalReferenceClassInstance1 = newStyleGlobalReferenceClass()
        newStyleClassReferenceClass = game.NewStyleSubclassViaClassReference
        newStyleClassReferenceClassInstance1 = newStyleClassReferenceClass()

        ## Verify that all the functions are callable before the reload.
        oldStyleNamespaceClassInstance1.Func()
        oldStyleGlobalReferenceClassInstance1.Func()
        newStyleNamespaceClassInstance1.Func()
        newStyleNamespaceClassInstance1.FuncSuper()
        newStyleGlobalReferenceClassInstance1.Func()
        newStyleGlobalReferenceClassInstance1.FuncSuper()
        newStyleClassReferenceClassInstance1.Func()

        self.ReloadScriptFile(scriptDirectory, scriptDirPath, "inheritanceSuperclasses.py")

        ## Call functions on the instances created pre-reload.
        self.failUnlessRaises(TypeError, oldStyleNamespaceClassInstance1.Func)  # A
        oldStyleGlobalReferenceClassInstance1.Func()
        self.failUnlessRaises(TypeError, newStyleNamespaceClassInstance1.Func)  # B
        newStyleNamespaceClassInstance1.FuncSuper()
        newStyleGlobalReferenceClassInstance1.Func()
        newStyleGlobalReferenceClassInstance1.FuncSuper()
        newStyleClassReferenceClassInstance1.Func()

        # A) Accessed the base class via namespace, got incompatible post-reload version.
        # B) Same as A.

        ## Create new post-reload instances of the subclasses.
        self.failUnlessRaises(TypeError, game.OldStyleSubclassViaNamespace)
        oldStyleGlobalReferenceClassInstance2 = game.OldStyleSubclassViaGlobalReference()
        self.failUnlessRaises(TypeError, game.NewStyleSubclassViaNamespace)
        newStyleGlobalReferenceClassInstance2 = game.NewStyleSubclassViaGlobalReference()
        newStyleClassReferenceClassInstance2 = game.NewStyleSubclassViaClassReference()

        # *) Fail for same reason as the calls to the pre-reload instances.

        ## Call functions on the instances created post-reload.
        # oldStyleNamespaceClassInstance2.Func()
        oldStyleGlobalReferenceClassInstance2.Func()
        # newStyleNamespaceClassInstance2.Func()
        # newStyleNamespaceClassInstance2.FuncSuper()
        newStyleGlobalReferenceClassInstance2.Func()
        newStyleGlobalReferenceClassInstance2.FuncSuper()
        newStyleClassReferenceClassInstance2.Func()

        ## Pre-reload instances get their base class replaced with the new version.
        self.UpdateBaseClass(oldStyleClass, game.OldStyleBase)
        self.UpdateBaseClass(newStyleClass, game.NewStyleBase)

        ## Call functions on the instances created pre-reload.
        oldStyleNamespaceClassInstance1.Func()                                          # A
        self.failUnlessRaises(TypeError, oldStyleGlobalReferenceClassInstance1.Func)    # B
        newStyleNamespaceClassInstance1.Func()                                          # C
        newStyleNamespaceClassInstance1.FuncSuper()
        self.failUnlessRaises(TypeError, newStyleGlobalReferenceClassInstance1.Func)    # D
        newStyleGlobalReferenceClassInstance1.FuncSuper()
        newStyleClassReferenceClassInstance1.Func()

        # A) Fixed, due to base class update.
        # B) The base class is now post-reload, the global reference still pre-reload.
        # C) Fixed, due to base class update.
        # D) The base class is now post-reload, the global reference still pre-reload.

        ## Call functions on the instances created post-reload.
        # oldStyleNamespaceClassInstance2.Func()
        self.failUnless(TypeError, oldStyleGlobalReferenceClassInstance2.Func)
        # newStyleNamespaceClassInstance2.Func()
        # newStyleNamespaceClassInstance2.FuncSuper()
        self.failUnlessRaises(TypeError, newStyleGlobalReferenceClassInstance2.Func)
        newStyleGlobalReferenceClassInstance2.FuncSuper()
        newStyleClassReferenceClassInstance2.Func()

        ## Create new post-reload post-update instances of the subclasses.
        oldStyleNamespaceClassInstance3 = game.OldStyleSubclassViaNamespace()
        self.failUnlessRaises(TypeError, game.OldStyleSubclassViaGlobalReference)
        newStyleNamespaceClassInstance3 = game.NewStyleSubclassViaNamespace()
        self.failUnlessRaises(TypeError, game.NewStyleSubclassViaGlobalReference)
        newStyleClassReferenceClassInstance3 = game.NewStyleSubclassViaClassReference()

        ## Call functions on the instances created post-reload post-update.
        oldStyleNamespaceClassInstance3.Func()
        #oldStyleGlobalReferenceClassInstance3.Func()
        newStyleNamespaceClassInstance3.Func()
        newStyleNamespaceClassInstance3.FuncSuper()
        #newStyleGlobalReferenceClassInstance3.Func()
        #newStyleGlobalReferenceClassInstance3.FuncSuper()
        newStyleClassReferenceClassInstance3.Func()

        logging.debug("Test updating global references for 'game.OldStyleBase'")
        self.UpdateGlobalReferences(oldStyleClass, game.OldStyleBase)
        logging.debug("Test updating global references for 'game.NewStyleBase'")
        self.UpdateGlobalReferences(newStyleClass, game.NewStyleBase)

        ### All calls on instances created at any point, should now work.
        ## Call functions on the instances created pre-reload.
        oldStyleNamespaceClassInstance1.Func()
        oldStyleGlobalReferenceClassInstance1.Func()
        newStyleNamespaceClassInstance1.Func()
        newStyleNamespaceClassInstance1.FuncSuper()
        newStyleGlobalReferenceClassInstance1.Func()
        newStyleGlobalReferenceClassInstance1.FuncSuper()
        newStyleClassReferenceClassInstance1.Func()

        ## Call functions on the instances created post-reload.
        # oldStyleNamespaceClassInstance2.Func()
        oldStyleGlobalReferenceClassInstance2.Func()
        # newStyleNamespaceClassInstance2.Func()
        # newStyleNamespaceClassInstance2.FuncSuper()
        newStyleGlobalReferenceClassInstance2.Func()
        newStyleGlobalReferenceClassInstance2.FuncSuper()
        newStyleClassReferenceClassInstance2.Func()

        ## Call functions on the instances created post-reload post-update.
        oldStyleNamespaceClassInstance3.Func()
        #oldStyleGlobalReferenceClassInstance3.Func()
        newStyleNamespaceClassInstance3.Func()
        newStyleNamespaceClassInstance3.FuncSuper()
        #newStyleGlobalReferenceClassInstance3.Func()
        #newStyleGlobalReferenceClassInstance3.FuncSuper()
        newStyleClassReferenceClassInstance3.Func()

        ### New instances from the classes should be creatable.
        ## Instantiate the classes.
        oldStyleNamespaceClassInstance4 = game.OldStyleSubclassViaNamespace()
        oldStyleGlobalReferenceClassInstance4 = game.OldStyleSubclassViaGlobalReference()
        newStyleNamespaceClassInstance4 = game.NewStyleSubclassViaNamespace()
        newStyleGlobalReferenceClassInstance4 = game.NewStyleSubclassViaGlobalReference()
        newStyleClassReferenceClassInstance4 = game.NewStyleSubclassViaClassReference()

        ## Call functions on the instances.
        oldStyleNamespaceClassInstance4.Func()
        oldStyleGlobalReferenceClassInstance4.Func()
        newStyleNamespaceClassInstance4.Func()
        newStyleNamespaceClassInstance4.FuncSuper()
        newStyleGlobalReferenceClassInstance4.Func()
        newStyleGlobalReferenceClassInstance4.FuncSuper()
        newStyleClassReferenceClassInstance4.Func()

    def testOverwriteSameFileClassReload(self):
        """
        Reloading approach: Overwrite old objects on reload.
        Reloading scope: Same file.
        
        1. Get references to the exported classes.
        2. Instantiate an instance from each class.
        3. Call the functions exposed by each instance.

        4. Reload the script the classes were exported from.

        5. Verify that the old classes were replaced with new ones.
        6. Call the functions exposed by each old class instance.
        7. Instantiate an instance of each new class.
        8. Call the functions exposed by each new class instance.

        This verifies that instances linked to old superceded
        versions of a class, still work.
        """
        scriptDirPath = GetScriptDirectory()
        cr = self.codeReloader = reloader.CodeReloader()
        cr.scriptDirectoryClass = ReloadableScriptDirectoryNoUnitTesting
        scriptDirectory = cr.AddDirectory("game", scriptDirPath)
        self.failUnless(scriptDirectory is not None, "Script loading failure")
        
        import game

        # Obtain references and instances for the classes defined in the script.
        oldStyleBaseClass = game.OldStyleBase
        oldStyleBaseClassInstance = oldStyleBaseClass()
        oldStyleClass = game.OldStyle
        oldStyleClassInstance = oldStyleClass()

        newStyleBaseClass = game.NewStyleBase
        newStyleBaseClassInstance = newStyleBaseClass()
        newStyleClass = game.NewStyle
        newStyleClassInstance = newStyleClass()

        # Verify that the exposed method can be called on each.
        oldStyleBaseClassInstance.Func()
        oldStyleClassInstance.Func()
        newStyleBaseClassInstance.Func()
        newStyleClassInstance.Func()
        newStyleClassInstance.FuncSuper()

        self.ReloadScriptFile(scriptDirectory, scriptDirPath, "inheritanceSuperclasses.py")

        # Verify that the original classes were replaced with new versions.
        self.failUnless(oldStyleBaseClass is not game.OldStyleBase, "Failed to replace the original 'game.OldStyleBase' class")
        self.failUnless(oldStyleClass is not game.OldStyle, "Failed to replace the original 'game.OldStyle' class")
        self.failUnless(newStyleBaseClass is not game.NewStyleBase, "Failed to replace the original 'game.NewStyleBase' class")
        self.failUnless(newStyleClass is not game.NewStyle, "Failed to replace the original 'game.NewStyle' class")

        # Verify that the exposed method can be called on the pre-existing instances.
        oldStyleBaseClassInstance.Func()
        oldStyleClassInstance.Func()
        newStyleBaseClassInstance.Func()
        newStyleClassInstance.Func()
        newStyleClassInstance.FuncSuper()

        # Make some new instances from the old class references.
        oldStyleBaseClassInstance = oldStyleBaseClass()
        oldStyleClassInstance = oldStyleClass()
        newStyleBaseClassInstance = newStyleBaseClass()
        newStyleClassInstance = newStyleClass()
        
        # Verify that the exposed method can be called on the new instances.
        oldStyleBaseClassInstance.Func()
        oldStyleClassInstance.Func()
        newStyleBaseClassInstance.Func()
        newStyleClassInstance.Func()
        newStyleClassInstance.FuncSuper()
        
        # Make some new instances from the new class references.
        oldStyleBaseClassInstance = game.OldStyleBase()
        oldStyleClassInstance = game.OldStyle()
        newStyleBaseClassInstance = game.NewStyleBase()
        newStyleClassInstance = game.NewStyle()
        
        # Verify that the exposed method can be called on the new instances.
        oldStyleBaseClassInstance.Func()
        oldStyleClassInstance.Func()
        newStyleBaseClassInstance.Func()
        newStyleClassInstance.Func()
        newStyleClassInstance.FuncSuper()

    def testUpdateSameFileReload_ClassFunctionUpdate(self):
        """
        Reloading approach: Update old objects on reload.
        Reloading scope: Same file.
        
        1. Get references to the exported classes.
        2. Get references to functions on those classes.

        3. Reload the script the classes were exported from.

        4. Verify the old classes have not been replaced.
        5. Verify the functions on the classes have been updated.

        This verifies the existing class functions are updated in place.
        """
        scriptDirPath = GetScriptDirectory()
        cr = self.codeReloader = reloader.CodeReloader(mode=reloader.MODE_UPDATE)
        cr.scriptDirectoryClass = ReloadableScriptDirectoryNoUnitTesting
        scriptDirectory = cr.AddDirectory("game", scriptDirPath)
        self.failUnless(scriptDirectory is not None, "Script loading failure")
        
        import game

        # Obtain references and instances for the classes defined in the script.
        oldStyleBaseClass = game.OldStyleBase
        newStyleBaseClass = game.NewStyleBase

        # Verify that the exposed method can be called on each.
        oldStyleBaseClassFunc = oldStyleBaseClass.Func_Arguments1
        newStyleBaseClassFunc = newStyleBaseClass.Func_Arguments1

        cb = MakeMangleFilenameCallback("inheritanceSuperclasses_FunctionUpdate.py")
        self.ReloadScriptFile(scriptDirectory, scriptDirPath, "inheritanceSuperclasses.py", mangleCallback=cb)

        ## Verify that the original classes were not replaced.
        # This is of course because their contents are updated.
        self.failUnless(oldStyleBaseClass is game.OldStyleBase, "Failed to keep the original 'game.OldStyleBase' class")
        self.failUnless(newStyleBaseClass is game.NewStyleBase, "Failed to keep the original 'game.NewStyleBase' class")

        ## Verify that the functions on the classes have been updated in place.
        # All classes should have had their functions replaced.
        self.failUnless(oldStyleBaseClassFunc.im_func is not oldStyleBaseClass.Func_Arguments1.im_func, "Class function not updated in place")
        self.failUnless(newStyleBaseClassFunc.im_func is not newStyleBaseClass.Func_Arguments1.im_func, "Class function not updated in place")

        ## Verify that the argument names are updated
        # Old style classes should work naturally.
        ret1 = inspect.getargspec(oldStyleBaseClassFunc.im_func)
        ret2 = inspect.getargspec(oldStyleBaseClass.Func_Arguments1.im_func)
        self.failUnless(ret1 != ret2, "Function arguments somehow not updated")

        ret1 = inspect.getargspec(newStyleBaseClassFunc.im_func)
        ret2 = inspect.getargspec(newStyleBaseClass.Func_Arguments1.im_func)
        self.failUnless(ret1 != ret2, "Function arguments somehow not updated")

        ret = inspect.getargspec(oldStyleBaseClass.Func_Arguments2.im_func)
        self.failUnless(ret[3] == (True,), "Function argument default value not updated")
        ret = inspect.getargspec(newStyleBaseClass.Func_Arguments2.im_func)
        self.failUnless(ret[3] == (True,), "Function argument default value not updated")

        # Note: Actually, all this cack is updated just by the function having been replaced in-situ.

    def testUpdateSameFileReload_ClassRemoval(self):
        """
        Reloading approach: Update old objects on reload.
        Reloading scope: Same file.
        
        1. Get references to the exported classes.
        2. Get references to functions on those classes.

        3. Reload the script the classes were exported from.

        4. Verify the old classes have not been replaced.
        5. Verify the functions on the classes have been replaced.

        This verifies the existing classes are updated in place.
        """
        scriptDirPath = GetScriptDirectory()
        cr = self.codeReloader = reloader.CodeReloader(mode=reloader.MODE_UPDATE)
        cr.scriptDirectoryClass = ReloadableScriptDirectoryNoUnitTesting
        scriptDirectory = cr.AddDirectory("game", scriptDirPath)
        self.failUnless(scriptDirectory is not None, "Script loading failure")
        
        import game

        # Obtain references and instances for the classes defined in the script.
        oldStyleBaseClass = game.OldStyleBase
        oldStyleClass = game.OldStyle
        newStyleBaseClass = game.NewStyleBase
        newStyleClass = game.NewStyle

        # Verify that the exposed method can be called on each.
        oldStyleBaseClassFunc = oldStyleBaseClass.Func
        oldStyleClassFunc = oldStyleClass.Func
        newStyleBaseClassFunc = newStyleBaseClass.Func
        newStyleClassFunc = newStyleClass.Func

        cb = MakeMangleFilenameCallback("inheritanceSuperclasses_ClassRemoval.py")
        newScriptFile = self.ReloadScriptFile(scriptDirectory, scriptDirPath, "inheritanceSuperclasses.py", mangleCallback=cb)

        ## Verify that the original classes were not replaced.
        # This is of course because their contents are updated.
        self.failUnless(oldStyleBaseClass is game.OldStyleBase, "Failed to keep the original 'game.OldStyleBase' class")
        self.failUnless(oldStyleClass is game.OldStyle, "Failed to keep the original 'game.OldStyle' class")
        self.failUnless(newStyleBaseClass is game.NewStyleBase, "Failed to keep the original 'game.NewStyleBase' class")
        self.failUnless(newStyleClass is game.NewStyle, "Failed to keep the original 'game.NewStyle' class")

        ## Verify that the functions on the classes have been updated in place.
        # All classes which still exist in the updated script should have had their functions replaced.
        self.failUnless(oldStyleBaseClassFunc.im_func is not oldStyleBaseClass.Func.im_func, "Class function not updated in place")
        self.failUnless(newStyleBaseClassFunc.im_func is not newStyleBaseClass.Func.im_func, "Class function not updated in place")
        self.failUnless(newStyleClassFunc.im_func is not newStyleClass.Func.im_func, "Class function not updated in place")

        # All classes which have been leaked should remain unchanged.
        self.failUnless(oldStyleClassFunc.im_func is oldStyleClass.Func.im_func, "Class function not updated in place")

    def testUpdateSameFileReload_ClassFunctionAddition(self):
        pass

    def testUpdateSameFileReload_ClassFunctionRemoval(self):
        pass

    def testUpdateSameFileReload_ClassAddition(self):
        pass

    def testUpdateSameFileReload_ClassRemoval(self):
        pass

    def testUpdateSameFileReload_FunctionUpdate(self):
        """
        Reloading approach: Update old objects on reload.
        Reloading scope: Same file.
        
        1. Get references to the exported functions.

        2. Reload the script the classes were exported from.

        3. Verify the old functions have been replaced.
        4. Verify the functions are callable.

        This verifies that new contributions are put in place.
        """
        scriptDirPath = GetScriptDirectory()
        cr = self.codeReloader = reloader.CodeReloader(mode=reloader.MODE_UPDATE)
        cr.scriptDirectoryClass = ReloadableScriptDirectoryNoUnitTesting
        scriptDirectory = cr.AddDirectory("game", scriptDirPath)
        self.failUnless(scriptDirectory is not None, "Script loading failure")
        
        import game

        # Obtain references and instances for the classes defined in the script.
        testFunction = game.TestFunction
        testFunction_PositionalArguments = game.TestFunction_PositionalArguments
        testFunction_KeywordArguments = game.TestFunction_KeywordArguments

        cb = MakeMangleFilenameCallback("functions_Update.py")
        newScriptFile = self.ReloadScriptFile(scriptDirectory, scriptDirPath, "functions.py", mangleCallback=cb)

        self.failUnless(testFunction is not game.TestFunction, "Function not updated by reload")
        self.failUnless(testFunction_PositionalArguments is not game.TestFunction_PositionalArguments, "Function not updated by reload")
        self.failUnless(testFunction_KeywordArguments is not game.TestFunction_KeywordArguments, "Function not updated by reload")

        ## Verify that the old functions still work, in case things hold onto references past reloads.
        ret = testFunction("testarg1")
        self.failUnless(ret[0] == "testarg1", "Old function failed after reload")
        
        ret = testFunction_PositionalArguments("testarg1", "testarg2", "testarg3")
        self.failUnless(ret[0] == "testarg1" and ret[1] == ("testarg2", "testarg3"), "Old function failed after reload")
        
        ret = testFunction_KeywordArguments(testarg1="testarg1")
        self.failUnless(ret[0] == "arg1" and ret[1] == {"testarg1":"testarg1"}, "Old function failed after reload")

        ## Verify that the new functions work.
        ret = game.TestFunction("testarg1")
        self.failUnless(ret[0] == "testarg1", "Updated function failed after reload")
        
        ret = game.TestFunction_PositionalArguments("testarg1", "testarg2", "testarg3")
        self.failUnless(ret[0] == "testarg1" and ret[1] == ("testarg2", "testarg3"), "Updated function failed after reload")
        
        ret = game.TestFunction_KeywordArguments(testarg1="testarg1")
        self.failUnless(ret[0] == "newarg1" and ret[1] == {"testarg1":"testarg1"}, "Updated function failed after reload")

    def testUpdateSameFileReload_ImportAddition(self):
        """
        This test is intended to verify that when a changed file adds an import
        statement, the imported object is present when it is reloaded.
        """
        ## PREPARATION:

        scriptDirPath = GetScriptDirectory()
        cr = self.codeReloader = reloader.CodeReloader(mode=reloader.MODE_UPDATE)
        cr.scriptDirectoryClass = ReloadableScriptDirectoryNoUnitTesting
        scriptDirectory = cr.AddDirectory("game", scriptDirPath)
        self.failUnless(scriptDirectory is not None, "Script loading failure")

        import game
        oldFunction = game.ImportTestClass.TestFunction.im_func
        self.failUnless("logging" not in oldFunction.func_globals, "Global entry unexpectedly already present")
        
        cb = MakeMangleFilenameCallback("import_Update.py")
        newScriptFile = self.ReloadScriptFile(scriptDirectory, scriptDirPath, "import.py", mangleCallback=cb)

        ## ACTUAL TESTS:

        newFunction = game.ImportTestClass.TestFunction.im_func
        self.failUnless("logging" in newFunction.func_globals, "Global entry unexpectedly already present")


class CodeReloaderSupportTests(CodeReloadingTestCase):
    mockedNamespaces = None

    def tearDown(self):
        super(self.__class__, self).tearDown()

        # Restore all the mocked namespace entries.
        if self.mockedNamespaces is not None:
            for namespacePath, replacedValue in self.mockedNamespaces.iteritems():
                moduleNamespace, attributeName = namespacePath.rsplit(".", 1)
                module = __import__(moduleNamespace)
                setattr(module, attributeName, replacedValue)

    def InsertMockNamespaceEntry(self, namespacePath, replacementValue):
        if self.mockedNamespaces is None:
            self.mockedNamespaces = {}

        moduleNamespace, attributeName = namespacePath.rsplit(".", 1)
        module = __import__(moduleNamespace)

        # Store the old value.
        if namespacePath not in self.mockedNamespaces:
            self.mockedNamespaces[namespacePath] = getattr(module, attributeName)

        setattr(module, attributeName, replacementValue)

    def WaitForScriptFileChange(self, cr, scriptDirectory, scriptPath, oldScriptFile, maxDelay=10.0):
        startTime = time.time()
        delta = time.time() - startTime
        while delta < maxDelay:
            ret = cr.internalFileMonitor.WaitForNextMonitoringCheck()
            if ret is None:
                return None

            delta = time.time() - startTime

            newScriptFile = scriptDirectory.FindScript(scriptPath)
            if newScriptFile is None:
                continue

            if oldScriptFile is None and newScriptFile is not None:
                return delta

            if oldScriptFile.version < newScriptFile.version:
                return delta

    def testDirectoryRegistration(self):
        """
        Verify that this function returns a registered handler for a parent
        directory, if there are any above the given file path.
        """
        #self.InsertMockNamespaceEntry("reloader.ReloadableScriptDirectory", DummyClass)
        #self.failUnless(reloader.ReloadableScriptDirectory is DummyClass, "Failed to mock the script directory class")

        currentDirPath = GetCurrentDirectory()
        # Add several directories to ensure correct results are returned.
        scriptDirPath1 = os.path.join(currentDirPath, "scripts1")
        scriptDirPath2 = os.path.join(currentDirPath, "scripts2")
        scriptDirPath3 = os.path.join(currentDirPath, "scripts3")
        scriptDirPaths = [ scriptDirPath1, scriptDirPath2, scriptDirPath3 ]
        handlersByPath = {}

        baseNamespaceName = "testns"

        class DummySubClass(DummyClass):
            def Load(self):
                return True

        dummySubClassInstance = DummySubClass()
        self.failUnless(dummySubClassInstance.Load() is True, "DummySubClass insufficient to fake directory loading")
        
        cr = reloader.CodeReloader()        
        cr.scriptDirectoryClass = DummySubClass

        # Test that a bad path will not find a handler when there are no handlers.
        self.failUnless(cr.FindDirectory("unregistered path") is None, "Got a script directory handler for an unregistered path")

        for scriptDirPath in scriptDirPaths:
            handler = cr.AddDirectory(baseNamespaceName, scriptDirPath)
            self.failUnless(handler is not None, "Script loading failure")
            handlersByPath[scriptDirPath] = handler
        
        # Test that a given valid registered script path gives the known handler for that path.
        while len(scriptDirPaths):
            scriptDirPath = scriptDirPaths.pop()
            fictionalScriptPath = os.path.join(scriptDirPath, "nonExistentScript.py")
            scriptDirectory = cr.FindDirectory(fictionalScriptPath)
            self.failUnless(scriptDirectory, "Got no script directory handler instance")
            self.failUnless(scriptDirectory is handlersByPath[scriptDirPath], "Got a different script directory handler instance")

        # Test that a bad path will not find a handler when there are valid ones for other paths.
        self.failUnless(cr.FindDirectory("unregistered path") is None, "Got a script directory handler for an unregistered path")

    def testAttributeLeaking(self):
        """
        This test is intended to exercise the leaked attribute tracking.

        First, a script is loaded exporting a class in a namespace.  Next the
        script is copied and the class is removed from it.  The modified copy
        is then reloaded in place of the original.  It is verified that:
        
        - The removed class is now present in the leaked attribute tracking.
        - The given leaked attribute is associated with the previous version
          of the script.
        - The class is still present in the namespace and is actually leaked.
        
        Lastly, a final copy of the script is made, with the class back in
        place.  This is then reloaded in place of the first copy.  It is
        verified that:
        
        - The namespace entry is no longer a leaked attribute.
        - The class in the namespace is not the original version.
        """
    
        ## PREPARATION:
    
        # The name of the attribute we are going to leak as part of this test.
        leakName = "NewStyleSubclassViaClassReference"
    
        scriptDirPath = GetScriptDirectory()
        cr = self.codeReloader = reloader.CodeReloader()
        cr.scriptDirectoryClass = ReloadableScriptDirectoryNoUnitTesting
        scriptDirectory = cr.AddDirectory("game", scriptDirPath)
        self.failUnless(scriptDirectory is not None, "Script loading failure")

        # Locate the script file object for the 'inheritanceSubclasses.py' file.
        scriptPath = os.path.join(scriptDirPath, "inheritanceSubclasses.py")
        oldScriptFile = scriptDirectory.FindScript(scriptPath)
        self.failUnless(oldScriptFile is not None, "Failed to find initial script file")

        namespacePath = oldScriptFile.namespacePath
        namespace = scriptDirectory.GetNamespace(namespacePath)
        leakingValue = getattr(namespace, leakName)

        #  - Attribute is removed from a new version of the script file.
        #    - Attribute appears in the leaked attributes dictionary of the new script file.
        #    - Attribute is still present in the namespace.

        newScriptFile1 = cr.CreateNewScript(oldScriptFile)
        self.failUnless(newScriptFile1 is not None, "Failed to create new script file version at attempt one")
        
        # Pretend that the programmer deleted a class from the script since the original load.
        del newScriptFile1.scriptGlobals[leakName]

        # Replace the old script with the new version.
        cr.UseNewScript(oldScriptFile, newScriptFile1)

        ## ACTUAL TESTS:

        self.failUnless(cr.IsAttributeLeaked(leakName), "Attribute not in leakage registry")

        # Ensure that the leakage is recorded as coming from the original script.
        leakedInVersion = cr.GetLeakedAttributeVersion(leakName)
        self.failUnless(leakedInVersion == oldScriptFile.version, "Attribute was leaked in %d, should have been leaked in %d" % (leakedInVersion, oldScriptFile.version))

        # Ensure that the leakage is left in the module.
        self.failUnless(hasattr(namespace, leakName), "Leaked attribute no longer present")
        self.failUnless(getattr(namespace, leakName) is leakingValue, "Leaked value differs from original value")

        ## PREPARATION:

        #  - Attribute was already leaked, and reload comes with no replacement.
        #    - New script file has leak entry propagated from old script file.
        #    - Attribute is still present in the namespace.

        newScriptFile2 = cr.CreateNewScript(newScriptFile1)
        self.failUnless(newScriptFile2 is not None, "Failed to create new script file version at attempt two")

        # Pretend that the programmer deleted a class from the script since the original load.
        del newScriptFile2.scriptGlobals[leakName]

        # Replace the old script with the new version.
        cr.UseNewScript(newScriptFile1, newScriptFile2)

        ## ACTUAL TESTS:

        self.failUnless(cr.IsAttributeLeaked(leakName), "Attribute not in leakage registry")

        # Ensure that the leakage is recorded as coming from the original script.
        leakedInVersion = cr.GetLeakedAttributeVersion(leakName)
        self.failUnless(leakedInVersion == oldScriptFile.version, "Attribute was leaked in %d, should have been leaked in %d" % (leakedInVersion, oldScriptFile.version))

        # Ensure that the leakage is left in the module.
        self.failUnless(hasattr(namespace, leakName), "Leaked attribute no longer present")
        self.failUnless(getattr(namespace, leakName) is leakingValue, "Leaked value differs from original value")
        
        ## PREPARATION:

        #  - Attribute was already leaked, and reload comes with an invalid replacement.
        #    - Reload is rejected.

        ## ACTUAL TESTS:

        logging.warn("TODO, implement leakage compatibility case")

        ## PREPARATION:

        #  - Attribute was already leaked, and reload comes with a valid replacement.
        #    - New script file lacks leak entry for attribute.
        #    - Attribute in namespace is value from new script file.

        newScriptFile3 = cr.CreateNewScript(newScriptFile2)
        self.failUnless(newScriptFile3 is not None, "Failed to create new script file version at attempt two")

        # Replace the old script with the new version.
        cr.UseNewScript(newScriptFile2, newScriptFile3)
        
        newValue = newScriptFile3.scriptGlobals[leakName]

        ## ACTUAL TESTS:

        self.failUnless(not cr.IsAttributeLeaked(leakName), "Attribute still in leakage registry")

        # Ensure that the leakage is left in the module.
        self.failUnless(hasattr(namespace, leakName), "Leaking attribute no longer present in the namespace")
        self.failUnless(getattr(namespace, leakName) is not leakingValue, "Leaked value is still contributed to the namespace")
        self.failUnless(getattr(namespace, leakName) is newValue, "New value is not contributed to the namespace")

        # Conclusion: Attribute leaking happens and is rectified.

    def testFileChangeDetection(self):
        """
        This test is intended to verify that file changes are detected and a reload takes place.
        """
    
        ## PREPARATION:

        scriptDirPath = GetScriptDirectory()
        scriptFilePath = os.path.join(scriptDirPath, "fileChange.py")
        script2DirPath = scriptDirPath +"2"
        
        self.failUnless(not os.path.exists(scriptFilePath), "Found script when it should have been deleted")

        # Start up the code reloader.
        # Lower the file change check frequency, to prevent unnecessary unit test stalling.
        cr = self.codeReloader = reloader.CodeReloader(monitorFileChanges=True, fileChangeCheckDelay=0.05)
        cr.scriptDirectoryClass = ReloadableScriptDirectoryNoUnitTesting
        scriptDirectory = cr.AddDirectory("game", scriptDirPath)
        self.failUnless(scriptDirectory is not None, "Script loading failure")

        # Identify the initial script to be loaded.
        sourceScriptFilePath = os.path.join(script2DirPath, "fileChange_Before.py")
        self.failUnless(os.path.exists(sourceScriptFilePath), "Failed to locate '%s' script" % sourceScriptFilePath)

        # Wait for the monitoring to kick in.
        ret = cr.internalFileMonitor.WaitForNextMonitoringCheck(maxDelay=10.0)
        self.failUnless(ret is not None, "File change not detected in a timely fashion (%s)" % ret)

        oldScriptFile = scriptDirectory.FindScript(scriptFilePath)
        self.failUnless(oldScriptFile is None, "Found the script file before it was created")

        open(scriptFilePath, "w").write(open(sourceScriptFilePath, "r").read())
        self.failUnless(os.path.exists(scriptFilePath), "Failed to create the scratch file")

        # Need to wait for the next second.  mtime is only accurate to the nearest second on *nix.
        mtime = os.stat(scriptFilePath).st_mtime
        while mtime == math.floor(time.time()):
            pass

        # Wait for the file creation to be detected.
        ret = self.WaitForScriptFileChange(cr, scriptDirectory, scriptFilePath, oldScriptFile)
        self.failUnless(ret is not None, "File change not detected in a timely fashion (%s)" % ret)

        import game
        self.failUnless(game.FileChangeFunction.__doc__ == " old version ", "Expected function doc string value not present")

        # Replace the initially loaded script contents via file operations.
        sourceScriptFilePath = os.path.join(script2DirPath, "fileChange_After.py")
        self.failUnless(os.path.exists(sourceScriptFilePath), "Failed to locate '%s' script" % sourceScriptFilePath)

        oldScriptFile = scriptDirectory.FindScript(scriptFilePath)
        self.failUnless(oldScriptFile is not None, "Did not find a loaded script file")

        ## BEHAVIOUR TO BE TESTED:

        # Change the monitored script.
        open(scriptFilePath, "w").write(open(sourceScriptFilePath, "r").read())
        
        # Wait for the next file change to be detected.
        ret = self.WaitForScriptFileChange(cr, scriptDirectory, scriptFilePath, oldScriptFile)
        self.failUnless(ret is not None, "File change not detected in a timely fashion (%s)" % ret)

        ## ACTUAL TESTS:

        newDocString = game.FileChangeFunction.__doc__
        self.failUnless(newDocString == " new version ", "Updated function doc string value '"+ newDocString +"'")

    def testScriptUnitTesting(self):
        """
        This test is intended to verify that local unit test failure equals code loading failure.
        
        First, the act of adding a directory containing a failing '*_unittest.py' file is
        tested.  The operation fails.  Next, the act of adding the same directory without
        the unit test failing is tested.  This now succeeds.
        """

        ## PREPARATION:

        scriptDirPath = GetScriptDirectory()
        self.codeReloader = reloader.CodeReloader()

        # We do not want to log the unit test failure we are causing.
        class NamespaceUnitTestFilter(logging.Filter):
            def __init__(self, *args, **kwargs):
                logging.Filter.__init__(self, *args, **kwargs)
                
                # These are the starting words of the lines we want to suppress.
                self.lineStartsWiths = [
                    "ScriptDirectory.Load",
                    "Error",
                    "Failure",
                    "Traceback",
                ]
                # How many lines we expect to have suppressed, for verification purposes.
                self.lineCount = len(self.lineStartsWiths)
                # Keep the suppressed lines around in case the filtering hits unexpected lines.
                self.filteredLines = []

            def filter(self, record):
                self.lineCount -= 1

                # If there are lines left to filter, check them.
                if len(self.lineStartsWiths):
                    txt = self.lineStartsWiths[0]
                    if record.msg.startswith(txt):
                        del self.lineStartsWiths[0]
                        self.filteredLines.append((record.msg, record.args))
                    else:
                        # Give up on filtering on unexpected input.
                        self.lineStartsWiths = []
                    return 0

                # Othewise, log away.
                return 1

        logger = logging.getLogger()
        loggingFilter = NamespaceUnitTestFilter("testScriptUnitTesting - logging Filter")
        # Make sure we remove this, otherwise the logging will leak..
        logger.addFilter(loggingFilter)

        ## BEHAVIOUR TO BE TESTED: Forced unit test and therefore operation failure.

        __builtins__.unitTestFailure = True
        try:
            scriptDirectory = self.codeReloader.AddDirectory("game", scriptDirPath)
        finally:
            logger.removeFilter(loggingFilter)
            del __builtins__.unitTestFailure

        ## ACTUAL TESTS:

        self.failUnless(scriptDirectory is None, "Unit tests unexpectedly passed")

        # If something went wrong with the filtered logging, log out the suppressed lines.
        if loggingFilter.lineCount != 0:
            for msg, args in loggingFilter.filteredLines:
                logging.error(msg, *args)
        # Fail unless the filtered logging met expectations.
        self.failUnless(loggingFilter.lineCount == 0, "Filtered too many lines to cover the unit test failure")

        ## BEHAVIOUR TO BE TESTED: Unit test passing and successful operation.

        __builtins__.unitTestFailure = False
        try:
            scriptDirectory = self.codeReloader.AddDirectory("game", scriptDirPath)
        finally:
            del __builtins__.unitTestFailure

        ## ACTUAL TESTS:

        self.failUnless(scriptDirectory is not None, "Unit tests unexpectedly failed")


class CodeReloadingLimitationTests(TestCase):
    """
    There are limitations to how well code reloading can work.
    
    This test case is intended to highlight these limitations so that they
    are known well enough to be worked with.
    """

    def testLocalVariableDirectModificationLimitation(self):
        """
        Demonstrate that local variables cannot be indirectly modified via locals().
        """
        def ModifyLocal():
            localValue = 1
            locals()["localValue"] = 2
            return localValue

        value = ModifyLocal()
        self.failUnless(value == 1, "Local variable unexpectedly indirectly modified")

        # Conclusion: Local variables are an unavoidable problem when code reloading.

    def testLocalVariableFrameModificationLimitation(self):
        """
        Demonstrate that local variables cannot be indirectly modified via frame references.
        """
        expectedValue = 1

        def ModifyLocal():
            localValue = expectedValue
            yield localValue
            yield localValue

        g = ModifyLocal()

        # Verify that the first generated value is the expected value.
        v = g.next()
        self.failUnless(v == expectedValue, "Initial local variable value %s, expected %d" % (v, expectedValue))

        f_locals = g.gi_frame.f_locals

        # Verify that the frame local value is the expected value.
        v = f_locals["localValue"]
        self.failUnless(v == expectedValue, "Indirectly referenced local variable value %s, expected %d" % (v, expectedValue))
        f_locals["localValue"] = 2

        # Verify that the frame local value pretended to change.
        v = f_locals["localValue"]
        self.failUnless(v == 2, "Indirectly referenced local variable value %s, expected %d" % (v, 2))

        # Verify that the second generated value is unchanged and still the expected value.
        v = g.next()
        self.failUnless(v == expectedValue, "Initial local variable value %s, expected %d" % (v, expectedValue))
        
        # Conclusion: Local variables are an unavoidable problem when code reloading.

    def testImmutableMethodModificationLimitation(self):
        """
        Demonstrate that methods are static, and cannot be updated in place.
        """
        class TestClass:
            def TestMethod(self):
                pass
        testInstance = TestClass()

        unboundMethod = TestClass.TestMethod
        self.failUnlessRaises(TypeError, lambda: setattr(unboundMethod, "im_class", self.__class__))

        boundMethod = testInstance.TestMethod
        self.failUnlessRaises(TypeError, lambda: setattr(boundMethod, "im_class", self.__class__))

        # Conclusion: Existing references to methods are an unavoidable problem when code reloading.


class DummyClass:
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        pass

    def __getattr__(self, attrName, defaultValue=None):
        if attrName.startswith("__"):
            return getattr(DummyClass, attrName)

        instance = self.__class__()
        instance.attrName = attrName
        instance.defaultValue = defaultValue
        return instance


def MakeMangleFilenameCallback(newFileName):
    """
    Encapsulate substituting a different script name.
    """
    def MangleFilenameCallback(scriptPath, newFileName):
        dirPath = os.path.dirname(scriptPath).replace("scripts", "scripts2")
        return os.path.join(dirPath, newFileName)
    return lambda scriptPath: MangleFilenameCallback(scriptPath, newFileName)

def GetCurrentDirectory():
    # There's probably a better way of doing this.
    dirPath = os.path.dirname(__file__)
    if not len(dirPath):
        dirPath = sys.path[0]
    return dirPath

def GetScriptDirectory():
    parentDirPath = GetCurrentDirectory()
    return os.path.join(os.path.dirname(parentDirPath), "scripts")

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)

    unittest.main()
