import ConfigParser

RANDOM_DEFAULT = "RANDOM_DEFAULT"

class IniSection(object):
    def __init__(self, sectionName, iniFile):
        self.__dict__["sectionName"] = sectionName
        #self.__dict__["configParser"] = iniFile.configParser
        self.__dict__["iniFile"] = iniFile

    def __getattr__(self, attrName):
        if attrName.startswith("__"):
            return object.__getattr__(self, attrName)

        try:
            return self.iniFile.configParser.get(self.sectionName,attrName)
        except ConfigParser.NoOptionError,e:
            raise AttributeError,attrName

    def getint(self, attrName, default=RANDOM_DEFAULT):
        try:
            return self.iniFile.configParser.getint(self.sectionName,attrName)
        except:
            if default == RANDOM_DEFAULT:
                raise
            return default
    def __setattr__(self, attrName, attrValue):
        # if getattr(self,attrName, None) != attrValue:
        self.iniFile.dirty = 1
        return self.iniFile.configParser.set(self.sectionName, attrName, attrValue)



class IniFile(object):
    def __init__(self, filename):
        self.configParser = ConfigParser.ConfigParser()
        self.filename = filename
        self.configParser.read([filename])
        self.dirty = 0

    def __getattr__(self, attrName):
        if attrName.startswith("__"):
            return object.__getattr__(self, attrName)
    
        if not self.configParser.has_section(attrName):
            self.configParser.add_section(attrName)
        inis = IniSection(attrName, self)
        setattr(self,attrName,inis)
        return inis

    def ShouldPersist(self):
        return self.dirty == 1

    def Persist(self):
        ob = file(self.filename,"w")
        self.configParser.write(ob)



