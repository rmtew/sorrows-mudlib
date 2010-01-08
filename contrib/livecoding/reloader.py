# Version: 2.01

import os
import sys
import logging
import types
import weakref
import time

logger = logging.getLogger("reloader")

import namespace

MODE_OVERWRITE = 1
MODE_UPDATE = 2

class NonExistentValue: pass

class ReloadableScriptFile(namespace.ScriptFile):
    version = 1

class ReloadableScriptDirectory(namespace.ScriptDirectory):
    scriptFileClass = ReloadableScriptFile
    unitTest = True


class CodeReloader:
    internalFileMonitor = None
    scriptDirectoryClass = ReloadableScriptDirectory

    def __init__(self, mode=MODE_OVERWRITE, monitorFileChanges=True, fileChangeCheckDelay=None):
        self.mode = mode
        self.monitorFileChanges = monitorFileChanges

        self.directoriesByPath = {}
        self.leakedAttributes = {}

        if monitorFileChanges:
            # Grabbing a weakref to a method of this instance requires me to
            # hold onto the method as well.
            pr = weakref.proxy(self)
            cb = lambda *args, **kwargs: pr.ProcessChangedFile(*args, **kwargs)
            self.internalFileMonitor = self.GetChangeHandler(cb, delay=fileChangeCheckDelay)

    def GetChangeHandler(self, cb, *args, **kwargs):
        import filechanges
        return filechanges.ChangeHandler(cb, *args, **kwargs)

    # ------------------------------------------------------------------------
    # Directory registration support.

    def AddDirectory(self, baseNamespace, baseDirPath):
        handler = self.scriptDirectoryClass(baseDirPath, baseNamespace)
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

        logger.debug("CreateNewScript namespace='%s', file='%s'", namespacePath, filePath)

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

            scriptDirectory.SetModuleAttributes(newScriptFile, namespace, overwritableAttributes=self.leakedAttributes)

            # Remove as leaks the attributes the new version contributed.
            self.RemoveLeakedAttributes(newScriptFile)
        elif self.mode == MODE_UPDATE:
            self.UpdateModuleAttributes(oldScriptFile, newScriptFile, namespace, overwritableAttributes=self.leakedAttributes)

            # Remove as leaks the attributes the new version contributed.
            self.RemoveLeakedAttributes(newScriptFile)

    def UpdateModuleAttributes(self, scriptFile, newScriptFile, namespace, overwritableAttributes=set()):
        logger.debug("UpdateModuleAttributes")

        moduleName = namespace.__name__
        filePath = newScriptFile.filePath
        
        # Track what files have contributed to the namespace.
        if filePath not in namespace.__file__:
            logger.error("On an update, a script file's path is expected to have already been registered")

        attributeChanges = {}

        # Collect existing values for entries.
        for k in scriptFile.contributedAttributes:
            v = getattr(namespace, k)
            valueType = type(v)
            attributeChanges[k] = [ (v, valueType), (NonExistentValue, None) ]

        # Collect entries for the attributes contributed by the new script file.
        for k, v, valueType in newScriptFile.GetExportableAttributes():
            if k not in attributeChanges:
                attributeChanges[k] = [ (NonExistentValue, None), (v, valueType) ]
            else:
                attributeChanges[k][1] = (v, valueType)

        # The globals dictionary of the retained original script file.
        globals_ = scriptFile.scriptGlobals

        contributedAttributes = set()
        leakedAttributes = set()

        for attrName, ((oldValue, oldType), (newValue, newType)) in attributeChanges.iteritems():
            # No new value -> the old value is being leaked.
            if newValue is NonExistentValue:
                leakedAttributes.add(attrName)
                continue

            if newType is types.ClassType or newType is types.TypeType:
                self.UpdateClass(oldValue, newValue, globals_)

                # If there was an old value, it is updated.
                if oldValue is not None:
                    continue

                # Otherwise, the new value is being added.
                newValue.__module__ = moduleName
                newValue.__file__ = filePath

                logger.debug("Encountered new class '%s'", attrName)
            elif oldType is newType and oldValue == newValue:
                # Skip constants whose value has not changed.
                logger.debug("Skippped unchanged attribute '%s'", attrName)
                continue
            elif isinstance(newValue, types.FunctionType):
                logger.debug("Rebound method '%s'", attrName)
                newValue = RebindFunction(newValue, globals_)
            elif isinstance(newValue, types.UnboundMethodType) or isinstance(newValue, types.MethodType):
                logger.debug("Rebound method '%s' to function", attrName)
                newValue = RebindFunction(newValue.im_func, globals_)

            # Build up the retained original globals with contributions.
            globals_[attrName] = newValue

            setattr(namespace, attrName, newValue)
            contributedAttributes.add(attrName)

        scriptFile.AddContributedAttributes(contributedAttributes)
        newScriptFile.SetContributedAttributes(contributedAttributes)

    def UpdateClass(self, value, newValue, globals_):
        if value is None:
            value = newValue

        logger.debug("Updating class %s, %s", value, id(value))

        for attrName, attrValue in newValue.__dict__.iteritems():
            if isinstance(attrValue, types.FunctionType):
                newAttrValue = RebindFunction(attrValue, globals_)
            elif isinstance(attrValue, types.UnboundMethodType) or isinstance(attrValue, types.MethodType):
                newAttrValue = RebindFunction(attrValue.im_func, globals_)
            else:
                # __doc__: On new-style classes, this cannot be overwritten.
                # __dict__: This makes no sense to overwrite.
                # __module__: Don't clobber the proper module name with '__builtin__'.
                # __weakref__: This makes no sense to overwrite.
                if attrName in ("__doc__", "__dict__", "__module__", "__weakref__"):
                    continue

                if value is not newValue:
                    newAttrValue = attrValue
                else:
                    continue

            logger.debug("setting %s %s", attrName, attrValue)
            setattr(value, attrName, attrValue)

    # ------------------------------------------------------------------------
    # Leaked attribute support

    def IsAttributeLeaked(self, attributeName):
        return attributeName in self.leakedAttributes

    def GetLeakedAttributeVersion(self, attributeName):
        return self.leakedAttributes[attributeName][1]

    def AddLeakedAttributes(self, oldScriptFile):
        filePath = oldScriptFile.filePath
    
        for attributeName in oldScriptFile.contributedAttributes:
            self.leakedAttributes[attributeName] = (filePath, oldScriptFile.version)

    def RemoveLeakedAttributes(self, newScriptFile):
        for attributeName in newScriptFile.contributedAttributes:
            if attributeName in self.leakedAttributes:
                del self.leakedAttributes[attributeName]

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
