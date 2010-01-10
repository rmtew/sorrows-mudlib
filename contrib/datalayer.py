import unittest, time, pickle, UserDict

class ColumnMetaData(object):
    def __init__(self):
        self.creationTime = time.time()
        self.lastReadTime = time.time()
        self.lastWriteTime = time.time()

class Table(object):
    lookupColumn = None

    def __init__(self, tableName):
        self.tableName = tableName
        self.creationTime = time.time()
        self.lastAccessTime = time.time()
        
        self.columnMetaData = {}
        self.rows = []

    def Lookup(self, key=Exception, value=Exception, transform=lambda v: v):
        matches = []
        for row in self.rows:
            if key is Exception or transform(getattr(row, key, Exception)) == value:
                row.lastAccessTime = time.time()
                matches.append(row)
        return matches

    def __getitem__(self, value):
        matches = self.Lookup(self.lookupColumn, value)
        if len(matches) > 1:
            raise Exception("Too many matches")

        if len(matches) == 0:
            raise KeyError(value)
        
        return matches[0]

    def AddRow(self):
        row = Row(self)
        self.rows.append(row)
        return row

    def OnColumnRead(self, columnName):
        metadata = self.columnMetaData.get(columnName, None)
        if metadata is None:
            self.columnMetaData[columnName] = ColumnMetaData()
        else:
            metadata.lastReadTime = time.time()

    def OnColumnWrite(self, columnName):
        metadata = self.columnMetaData.get(columnName, None)
        if metadata is None:
            self.columnMetaData[columnName] = ColumnMetaData()
        else:
            metadata.lastWriteTime = time.time()

class Row(object):
    def __init__(self, table):
        self.table = table

        self.creationTime = time.time()
        self.lastAccessTime = time.time()
        self.columns = {}

    def __getattr__(self, attrName, value=None):
        if attrName.startswith("__"):
            return object.__getattr__(self, attrName)

        if attrName in self.__dict__:
            return self.__dict__[attrName]

        if attrName in self.columns:
            self.table.OnColumnRead(attrName)

        self.lastAccessTime = time.time()
        return self.columns[attrName]

    def __setattr__(self, attrName, value):
        # If "columns" does not exist, __init__ is still executing.        
        if "columns" not in self.__dict__ or attrName in self.__dict__:
            return object.__setattr__(self, attrName, value)

        self.table.OnColumnWrite(attrName)

        self.columns[attrName] = value
        self.lastAccessTime = time.time()

class DataLayer(object):
    def __init__(self):
        self.tables = {}

    def GetTable(self, tableName):
        table = self.tables.get(tableName, None)
        if table is None:
            table = self.tables[tableName] = Table(tableName)
        return table

    def TableExists(self, tableName):
        return tableName in self.tables

    def __getattr__(self, attrName, value=None):
        if attrName.startswith("__") or attrName in self.__dict__:
            return object.__getattr__(self, attrName)
            
        return self.GetTable(attrName)


## Unit tests.

class RowTests(unittest.TestCase):
    def setUp(self):
        self.store = DataLayer()

    def testRowCreation(self):
        table = self.store.test

        # Verify that the row does not exist.
        matches = table.Lookup("key", "value")
        self.failUnless(not len(matches), "Retrieved row is not valid")

        row = table.AddRow()
        
        matches = table.Lookup()
        self.failUnless(len(matches), "Failed to find the new row")

    def testColumnCreation(self):
        table = self.store.test
        row = table.AddRow()
        row.key = "value"
        
        self.failUnless(row.key == "value", "Stored value is incorrect")

    def testRowLookup(self):
        table = self.store.test
        row = table.AddRow()
        row.key = "value"

        matches = table.Lookup("key", "value")
        self.failUnless(len(matches) == 1, "The new row was not entered into its table")
        self.failUnless(row is matches[0], "The new row is not the stored row")
        self.failUnless(row.key == "value", "The new row column does not have the assigned value")

class TableTests(unittest.TestCase):
    def setUp(self):
        self.store = DataLayer()

    def testTableExists(self):
        table = self.store.test
        self.failUnless(self.store.TableExists("test"), "TableExists is broken")

    def testTableCreation(self):
        # Verify that the table does not already exist.
        self.failUnless(not self.store.TableExists("test"), "Table already exists")

        # Verify that the two forms of access create and return the same table.
        indirectTable = self.store.GetTable("test")
        directTable = self.store.test
        self.failUnless(indirectTable is directTable, "Different tables retrieved")

    def testTableLookupTransform(self):
        table = self.store.test
        
        row = table.AddRow()
        row.label = "sample"
        
        row = table.AddRow()
        row.label = "saMple"

        row = table.AddRow()
        row.label = "SAMPLE"

        matches = table.Lookup("label", "SamplE")
        self.failUnless(len(matches) == 0, "Unexpected matches with no transform")

        matches = table.Lookup("label", "SAMPLE")
        self.failUnless(len(matches) == 1, "Not a single match with no transform")

        matches = table.Lookup("label", "SAMPLE", transform=lambda v: v.lower())
        self.failUnless(len(matches) == 0, "Unexpected matches with a bad transform")

        matches = table.Lookup("label", "SAMPLE", transform=lambda v: v.upper())
        self.failUnless(len(matches) == 3, "Not three matches with a good transform")

    def testTableLookupSyntax(self):
        table = self.store.test
        table.lookupColumn = "key"
        
        for i in range(10):
            row = table.AddRow()
            row.key = i
            row.label = str(i)

        self.failUnlessRaises(KeyError, lambda: table[20])

        row = table[4]
        self.failUnless(row.key == 4, "Row index column has incorrect value")
        self.failUnless(row.label == "4", "Row string column has incorrect value")        

class PersistenceTests(unittest.TestCase):
    def testRowPersistence(self):
        table = UserDict.UserDict()    
        table.OnColumnWrite = lambda *args: None
        table.OnColumnRead = lambda *args: None

        row = Row(table)
        row.one = 1
        row.string = "string"

        s = pickle.dumps(row)
        restoredRow = pickle.loads(s)

        self.failUnless(isinstance(row.table, UserDict.UserDict), "Row table reference incorrect")
        self.failUnless(len(row.columns) == 2, "Not just two columns in the unpersisted row")
        self.failUnless(row.one == 1, "'one' column has incorrect value")
        self.failUnless(row.string == "string", "'string' column has incorrect value")        

    def testStorePersistence(self):
        originalStore = DataLayer()
        row = originalStore.test.AddRow()
        row.one = 1
        row.string = "string"
        
        s = pickle.dumps(originalStore)        
        restoredStore = pickle.loads(s)
        
        self.failUnless(len(restoredStore.tables) == 1, "Not just one table restored")
        self.failUnless(restoredStore.TableExists("test"), "Restored table a different one than expected")
        
        table = restoredStore.test
        rows = table.Lookup()
        row = rows[0]
        self.failUnless(len(rows) == 1, "Not just one row restored")
        self.failUnless(row.table is table, "Row table reference incorrect")
        self.failUnless(len(row.columns) == 2, "Not just two columns in the unpersisted row")
        self.failUnless(row.one == 1, "'one' column has incorrect value")
        self.failUnless(row.string == "string", "'string' column has incorrect value")


if __name__ == "__main__":    
    unittest.main()
