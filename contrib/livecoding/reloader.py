# Version: 2.01

import os
import sys
import logging
import types
import weakref
import time
import gc
import traceback

logger = logging.getLogger("reloader")
#logger.setLevel(logging.DEBUG)

# TODO: rename 'namespace.py' to 'namespaces.py' ... need to think about it...
import namespace as namespaces

MODE_OVERWRITE = 1
MODE_UPDATE = 2

class NonExistentValue: pass

class ReloadableScriptFile(namespaces.ScriptFile):
    version = 1

class ReloadableScriptDirectory(namespaces.ScriptDirectory):
    scriptFileClass = ReloadableScriptFile
    unitTest = True


class CodeReloader:
    internalFileMonitor = None
    scriptDirectoryClass = ReloadableScriptDirectory

    def __init__(self, mode=MODE_UPDATE, monitorFileChanges=True, fileChangeCheckDelay=None):
        self.mode = mode
        self.monitorFileChanges = monitorFileChanges

        self.directoriesByPath = {}
        self.namespaceLeaks = {}
        self.classCreationCallback = None
        self.classUpdateCallback = None
        self.validateScriptCallback = None

        if monitorFileChanges:
            # Grabbing a weakref to a method of this instance requires me to
            # hold onto the method as well.
            pr = weakref.proxy(self)
            cb = lambda *args, **kwargs: pr.ProcessChangedFile(*args, **kwargs)
            self.internalFileMonitor = self.GetChangeHandler(cb, delay=fileChangeCheckDelay)

    def GetChangeHandler(self, cb, *args, **kwargs):
        import filechanges
        return filechanges.ChangeHandler(cb, *args, **kwargs)

    def EndMonitoring(self):
        if self.monitorFileChanges:
            self.internalFileMonitor = None

    def SetClassUpdateCallback(self, ob):
        if type(ob) is types.MethodType:
            self.classUpdateCallback = (weakref.proxy(ob.im_self), ob.func_name)
        elif type(ob) is types.FunctionType:
            self.classUpdateCallback = weakref.proxy(ob)
        elif ob is None:
            self.classUpdateCallback = ob           
        else:
            raise Exception("Bad callback")

    def SetClassCreationCallback(self, ob):
        if type(ob) is types.MethodType:
            self.classCreationCallback = (weakref.proxy(ob.im_self), ob.func_name)
        elif type(ob) is types.FunctionType:
            self.classCreationCallback = weakref.proxy(ob)
        elif ob is None:
            self.classCreationCallback = ob           
        else:
            raise Exception("Bad callback")

        for handler in self.directoriesByPath.itervalues():
            handler.SetClassCreationCallback(self.classCreationCallback)

    def SetValidateScriptCallback(self, ob):
        if type(ob) is types.MethodType:
            self.validateScriptCallback = (weakref.proxy(ob.im_self), ob.func_name)
        elif type(ob) is types.FunctionType:
            self.validateScriptCallback = weakref.proxy(ob)
        elif ob is None:
            self.validateScriptCallback = ob           
        else:
            raise Exception("Bad callback")

        for handler in self.directoriesByPath.itervalues():
            handler.SetValidateScriptCallback(self.validateScriptCallback)

    # ------------------------------------------------------------------------
    # Directory registration support.

    def AddDirectory(self, baseNamespace, baseDirPath):
        handler = self.scriptDirectoryClass(baseDirPath, baseNamespace, delScriptGlobals=(self.mode == MODE_UPDATE))
        if self.classCreationCallback:
            handler.SetClassCreationCallback(self.classCreationCallback)
        if self.validateScriptCallback:
            handler.SetValidateScriptCallback(self.validateScriptCallback)

        if handler.Load():
            self.directoriesByPath[baseDirPath] = handler
            logger.info("Added '%s' into '%s'", baseDirPath, baseNamespace)

            if self.monitorFileChanges:
                logger.info("Monitoring file changes for '%s'", baseDirPath)
                self.internalFileMonitor.AddDirectory(baseDirPath)

            return handler

        # Remove the namespace contributions which came from this failed process.
        handler.Unload()

    def RemoveDirectory(self, baseDirPath):
        if self.monitorFileChanges:
            self.internalFileMonitor.RemoveDirectory(baseDirPath)

        handler = self.directoriesByPath[baseDirPath]
        handler.Unload()

        del self.directoriesByPath[baseDirPath]

    def FindDirectory(self, filePath):
        filePathLower = filePath.lower()
        for dirPath, scriptDirectory in self.directoriesByPath.iteritems():
            if filePathLower.startswith(dirPath.lower()):
                return scriptDirectory

    # ------------------------------------------------------------------------
    # External events.

    def ProcessChangedFile(self, filePath, added=False, changed=False, deleted=False):
        logger.debug("File change '%s' added=%s changed=%s deleted=%s", filePath, added, changed, deleted)

        scriptDirectory = self.FindDirectory(filePath)
        if scriptDirectory is None:
            logger.error("File change event for invalid path '%s'", filePath)
            return

        oldScriptFile = scriptDirectory.FindScript(filePath)
        if oldScriptFile:
            # Modified or deleted.
            if changed:
                logger.info("Script reloaded '%s'", filePath)
                self.ReloadScript(oldScriptFile)
            elif deleted:
                logger.info("Script removed '%s'", filePath)
                logger.warn("Deleted script leaking its namespace contributions")
        else:
            if added:
                logger.info("Script loaded '%s'", filePath)
                self.LoadScript(filePath)
            elif changed:
                logger.error("Modified script not already loaded '%s'", filePath)
            elif deleted:
                logger.error("Deleted script not already loaded '%s'", filePath)

    # ------------------------------------------------------------------------
    # Script reloading support.

    def LoadScript(self, scriptFilePath):
        logger.debug("LoadScript")

        dirPath = os.path.dirname(scriptFilePath)
        scriptDirectory = self.FindDirectory(scriptFilePath)    
        namespace = scriptDirectory.GetNamespacePath(dirPath)
        scriptFile = scriptDirectory.LoadScript(scriptFilePath, namespace)
        ret = scriptDirectory.RunScript(scriptFile)
        if ret:
            scriptDirectory.RegisterScript(scriptFile)
        else:
            scriptFile.LogLastError()
        return ret            

    def ReloadScript(self, oldScriptFile):
        logger.debug("ReloadScript")
        
        newScriptFile = self.CreateNewScript(oldScriptFile)
        if newScriptFile is None:
            return False

        self.UseNewScript(oldScriptFile, newScriptFile)        
        return True

    def CreateNewScript(self, oldScriptFile):
        filePath = oldScriptFile.filePath
        namespacePath = oldScriptFile.namespacePath

        logger.debug("CreateNewScript namespace='%s', file='%s', oldVersion=%d", namespacePath, filePath, oldScriptFile.version)

        # Read in and compile the modified script file.
        scriptDirectory = self.FindDirectory(filePath)
        newScriptFile = scriptDirectory.LoadScript(filePath, namespacePath)

        # Try and execute the new script file.
        if scriptDirectory.RunScript(newScriptFile, tentative=True):
            # Before we can go ahead and use the new version of the script file,
            # we need to verify that it is suitable for use.  That it ran without
            # error is a good start.  But we also need to verify that the
            # attributes provided by each are compatible.
            if self.ScriptCompatibilityCheck(oldScriptFile, newScriptFile):
                newScriptFile.version = oldScriptFile.version + 1
                return newScriptFile
        else:
            # The execution failed, log context for the programmer to examine.
            newScriptFile.LogLastError()

        return None

    def UseNewScript(self, oldScriptFile, newScriptFile):
        logger.debug("UseNewScript")

        filePath = newScriptFile.filePath
        namespacePath = newScriptFile.namespacePath

        # The new version of the script being returned, means that it is
        # has been checked and approved for use.
        scriptDirectory = self.FindDirectory(filePath)

        # Leak the attributes the old version contributed.
        self.AddLeakedAttributes(oldScriptFile)

        # Insert the attributes from the new script file, allowing overwriting
        # of entries contributed by the old script file.
        namespace = scriptDirectory.GetNamespace(namespacePath)
        if self.mode == MODE_OVERWRITE:
            scriptDirectory.UnregisterScript(oldScriptFile)
            scriptDirectory.RegisterScript(newScriptFile)

            scriptDirectory.SetModuleAttributes(newScriptFile, namespace, overwritableAttributes=self.namespaceLeaks)

            # Remove as leaks the attributes the new version contributed.
            self.RemoveLeakedAttributes(newScriptFile)
        elif self.mode == MODE_UPDATE:
            self.UpdateModuleAttributes(oldScriptFile, newScriptFile, namespace, overwritableAttributes=self.namespaceLeaks)
            oldScriptFile.version += 1

            # Remove as leaks the attributes the new version contributed.
            self.RemoveLeakedAttributes(newScriptFile)

    # overwritableAttributes: why is this passed in?
    def UpdateModuleAttributes(self, scriptFile, newScriptFile, namespace, overwritableAttributes=set()):
        logger.debug("UpdateModuleAttributes")

        moduleName = namespace.__name__
        filePath = newScriptFile.filePath
        
        # Track what files have contributed to the namespace.
        if filePath not in namespace.__file__:
            logger.error("On an update, a script file's path is expected to have already been registered")

        attributeChanges = {}

        # Collect existing values for entries.
        for k in scriptFile.namespaceContributions:
            v = getattr(namespace, k)
            valueType = type(v)
            attributeChanges[k] = [ (v, valueType), (NonExistentValue, None) ]

        # Collect entries for the attributes imported or defined by the new script file.
        for k, v, valueType, exportable in newScriptFile.GetExportableAttributes():
            if exportable:
                if hasattr(namespace, k) and k not in overwritableAttributes and k != "__doc__":
                    logger.error("Duplicate namespace contribution for '%s.%s' from '%s', our class = %s", moduleName, k, scriptFile.filePath, v.__file__ == scriptFile.filePath)
                    continue

                if k not in attributeChanges:
                    attributeChanges[k] = [ (NonExistentValue, None), (v, valueType) ]
                else:
                    attributeChanges[k][1] = (v, valueType)
            else:
                if k in scriptFile.scriptGlobals:
                    logger.debug("Updated a non-exported global: %s %s", k, valueType)
                else:
                    logger.debug("Added a non-exported global: %s %s", k, valueType)
                scriptFile.scriptGlobals[k] = v

        # The globals dictionary of the retained original script file.
        globals_ = scriptFile.scriptGlobals

        namespaceContributions = set()

        for attrName, ((oldValue, oldType), t2) in attributeChanges.iteritems():
            newValue, newType = t2
        
            # No new value -> the old value is being leaked.
            if newValue is NonExistentValue:
                continue

            if newType is types.ClassType or newType is types.TypeType:
                self.UpdateClass(scriptFile, oldValue, newValue, globals_)

                instances = self.FindClassInstances(newValue)
                if len(instances):
                    logger.warn("Found %d instances of the %s class that will be in the wild" % (len(instances), newValue.__name__))
                    # Try and patch the instances, in a naive way.
                    # - Should really check that oldValue is suited for use.
                    for instance in instances:
                        instance.__class__ = oldValue

                # If there was an old value, it is updated.
                if oldValue and oldValue is not NonExistentValue:
                    logger.debug("Encountered existing class '%s' %s", attrName, oldValue)
                    namespaceContributions.add(attrName)
                    continue

                # Otherwise, the new value is being added.
                newValue.__module__ = moduleName
                newValue.__file__ = filePath

                logger.debug("Encountered new class '%s'", attrName)
            elif oldType is newType and oldValue == newValue:
                # Skip constants whose value has not changed.
                logger.debug("Skipped unchanged attribute '%s'", attrName)
                continue
            elif isinstance(newValue, types.FunctionType):
                logger.debug("Updated and rebound function '%s'", attrName)
                newValue = RebindFunction(newValue, globals_)
            elif isinstance(newValue, types.UnboundMethodType) or isinstance(newValue, types.MethodType):
                logger.debug("Updated and rebound method '%s' to function", attrName)
                newValue = RebindFunction(newValue.im_func, globals_)
            else:
                logger.debug("Updated changed attribute '%s'", attrName)

            # Build up the retained original globals with contributions.
            globals_[attrName] = newValue

            setattr(namespace, attrName, newValue)
            namespaceContributions.add(attrName)

        scriptFile.AddNamespaceContributions(namespaceContributions)
        newScriptFile.SetNamespaceContributions(namespaceContributions)

    def UpdateClass(self, scriptFile, value, newValue, globals_):
        logger.debug("Updating class %s:%s from %s:%s", value, hex(id(value)), newValue, hex(id(newValue)))

        if value is None or value is NonExistentValue:
            authoritativeValue = newValue
        else:
            authoritativeValue = value

        for attrName, attrValue in newValue.__dict__.iteritems():
            if isinstance(attrValue, types.FunctionType):
                attrValue = RebindFunction(attrValue, globals_)
            elif isinstance(attrValue, types.UnboundMethodType) or isinstance(attrValue, types.MethodType):
                attrValue = RebindFunction(attrValue.im_func, globals_)
            elif isinstance(attrValue, property):
                fget, fset, fdel = attrValue.fget, attrValue.fset, attrValue.fdel
                if fget:
                    fget = RebindFunction(fget, globals_)
                if fset:
                    fset = RebindFunction(fset, globals_)
                if fdel:
                    fdel = RebindFunction(fdel, globals_)
                attrValue = property(fget, fset, fdel, attrValue.__doc__)
            else:
                # __doc__: On new-style classes, this cannot be overwritten.
                # __dict__: This makes no sense to overwrite.
                # __module__: Don't clobber the proper module name with '__builtin__'.
                # __weakref__: This makes no sense to overwrite.
                if attrName in ("__doc__", "__dict__", "__module__", "__weakref__"):
                    continue

                if authoritativeValue is newValue:
                    continue

            logger.debug("setting %s %s", attrName, attrValue)
            setattr(authoritativeValue, attrName, attrValue)

        if value is None or value is NonExistentValue:
            scriptDirectory = self.FindDirectory(scriptFile.filePath)    
            scriptDirectory.BroadcastClassCreationEvent(newValue)
        else:
            if self.classUpdateCallback:
                try:
                    if type(self.classUpdateCallback) is tuple:
                        getattr(self.classUpdateCallback[0], self.classUpdateCallback[1])(value)
                    else:
                        self.classUpdateCallback(value)
                except ReferenceError:
                    self.classUpdateCallback = None
                except Exception:
                    logger.exception("Error broadcasting class update")

    def FindClassInstances(self, class_, *knownReferences):
        #cGlobals = None
        #for v in class_.__dict__.itervalues():
        #    if type(v) is types.FunctionType:
        #        cGlobals = v.func_globals
        #        break
    
        instances = []
        referrers1 = gc.get_referrers(class_)
        for referrer1 in referrers1:
            if type(referrer1) is types.InstanceType or type(referrer1) is class_:
                instances.append(referrer1)

                #referrers2 = gc.get_referrers(referrer1)
                #for referrer2 in referrers2:
                #    if referrer2 in [ instances, referrers2, sys._getframe(), cGlobals, referrers1 ]:
                #        continue
                #    if referrer2 in knownReferences:
                #        continue

                #    print id(referrer1), "REFERRER2", type(referrer2), hex(id(cGlobals))
                #    if type(referrer2) is list:
                #        # print "LIST", self.CountReferences(referrer2, 0, referrers2, *knownReferences), [ x for x in referrer2 ], "LIST_"
                #        print "LIST", [ x for x in referrer2 ], "LIST_"
                #    elif type(referrer2) is tuple:
                #        # print "TUPLE", self.CountReferences(referrer2, 0, referrers2, *knownReferences), [ x for x in referrer2 ], "TUPLE_"
                #        print "TUPLE", hex(id(referrer2)), [ x for x in referrer2 ], "TUPLE_", [ hex(id(v)) for v in knownReferences ]
                #    elif type(referrer2) is dict:
                #        if "__file__" in referrer2:
                #            print "MODULE-DICT", referrer2["__file__"]
                #        else:
                #            print "DICT", hex(id(referrer2)), referrer2.keys()
                #    else:
                #        print "????", type(referrer2)
        return instances

    # ------------------------------------------------------------------------
    # Leaked attribute support

    def IsAttributeLeaked(self, attributeName):
        return attributeName in self.namespaceLeaks

    def GetLeakedAttributeVersion(self, attributeName):
        return self.namespaceLeaks[attributeName][1]

    def AddLeakedAttributes(self, oldScriptFile):
        filePath = oldScriptFile.filePath
    
        for attributeName in oldScriptFile.namespaceContributions:
            self.namespaceLeaks[attributeName] = (filePath, oldScriptFile.version)

    def RemoveLeakedAttributes(self, newScriptFile):
        for attributeName in newScriptFile.namespaceContributions:
            if attributeName in self.namespaceLeaks:
                del self.namespaceLeaks[attributeName]

    # ------------------------------------------------------------------------
    # Attribute compatibility support

    def ScriptCompatibilityCheck(self, oldScriptFile, newScriptFile):
        logger.debug("ScriptCompatibilityCheck '%s'", oldScriptFile.filePath)

        # Do not allow replacement of old contributions, whether from the old
        # script file given, or contributions it has inherited itself, if the
        # new contributions are not compatible.
        pass
        # Overwrite:
        # - Different types.
        # Update:
        # - Change from old style class to new style class.
        return True


class StacklessCodeReloader(CodeReloader):
    def GetChangeHandler(self, cb, *args, **kwargs):
        kwargs["useThreads"] = False

        import filechanges
        return filechanges.ChangeHandler(cb, *args, **kwargs)

    def DispatchPendingFileChanges(self):
        self.internalFileMonitor.ProcessFileEvents()


def RebindFunction(function, globals_):
    newFunction = types.FunctionType(function.func_code, globals_, function.func_name, function.func_defaults)
    newFunction.__doc__= function.__doc__
    newFunction.__dict__.update(function.__dict__)
    return newFunction


# Upgrade Python versions less than 2.5...
if not hasattr(os.path, "relpath"):
    # If this is being run on earlier versions of Python than 2.6, monkeypatch 
    # in something resembling missing standard library functionality.
    if sys.version_info[0] == 2 and sys.version_info[1] < 6:
        def relpath(longPath, basePath):
            if not longPath.startswith(basePath):
                raise RuntimeError("Unexpected arguments")
            if longPath == basePath:
                return "."
            i = len(basePath)
            if not basePath.endswith(os.path.sep):
                i += len(os.path.sep)
            return longPath[i:]

        os.path.relpath = relpath
