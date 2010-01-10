import os, cPickle, datalayer
from mudlib import Service
from mudlib.services.data import IniFile


class DataService(Service):
    __sorrows__ = 'data'
    

    def Run(self):
        self.savePath = os.path.join(sorrows.services.gameDataPath, "gamedata.db")
        
        if os.path.exists(self.savePath):
            self.store = cPickle.load(open(self.savePath, 'rb'))
        else:
            self.store = datalayer.DataLayer()

        self.config = IniFile("config.ini")

    def OnStop(self):
        self.Persist()

        if self.config.ShouldPersist():
            self.config.Persist()

    def Persist(self):
        cPickle.dump(self.store, open(self.savePath, 'wb'))
