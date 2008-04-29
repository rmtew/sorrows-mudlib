import os
import cPickle
from mudlib import Service
from mudlib.services.data import DataTable, IniFile


class DataService(Service):
    __sorrows__ = 'data'

    def Run(self):
        self.tablesSavePath = sorrows.services.gameDataPath +"tables.db"
        self.tableSavePathTemplate = sorrows.services.gameDataPath +"%s.db"

        # If the persistance dump file exists, then read it in.
        d = self.UnpersistData(self.tablesSavePath)
        if d.has_key("tables"):
            self.tables = d["tables"]
        else:
            self.tables = {}
            self.Persist()
        # print 'Data service has', len(self.tables), 'tables.'
        self.tablesByName = {}

        # XXX

        self.config = IniFile("config.ini")

    def TableExists(self, tableName):
        return self.tables.has_key(tableName)

    def AddTable(self, tableName, columnNames):
        if self.tables.has_key(tableName):
            raise RuntimeError("TableExists", tableName)
        tableOb = DataTable(columnNames, [])
        self.tables[tableName] = 1
        self.tablesByName[tableName] = tableOb
        return tableOb

    def GetTable(self, tableName):
        if not self.tables.has_key(tableName):
            raise RuntimeError("TableDoesNotExist", tableName)
        f = open(self.tableSavePathTemplate % tableName, 'rb')
        tableOb = cPickle.load(f)
        f.close()
        self.tablesByName[tableName] = tableOb
        return tableOb

    def OnStop(self):
        self.Persist()
        self.PersistModifiedTables()

        if self.config.ShouldPersist():
            self.config.Persist()

    def Persist(self):
        self.PersistData(self.tablesSavePath, { "tables": self.tables })

    def PersistModifiedTables(self):
        for tableName, tableOb in self.tablesByName.items():
            if tableOb.modified:
                self.PersistTable(tableName)

    def PersistTable(self, tableName):
        tableOb = self.tablesByName[tableName]

        f = open(self.tableSavePathTemplate % tableName, 'wb')
        cPickle.dump(tableOb, f, 1)
        f.close()

        if tableOb.modified:
            del tableOb.modified
