class DataTable:
    idColumn = None
    idValue = None

    modified = 0

    def __init__(self, header, rows):
        self.header = header
        self.rows = rows

        self.modified = 1

    def SetIdColumn(self, columnName, value=1):
        self.idColumn = columnName
        self.idValue = value

    def GetRowID(self, row):
        return row[self.header.index(self.idColumn)]

    def GetColumnIdx(self, columnName):
        return self.header.index(columnName)

    def AddRow(self, row):
        retVal = None
        if self.idColumn is not None:
            retVal = self.idValue
            self.idValue += 1
            l = [ retVal ]
            l.extend(row)
            row = tuple(l)
            if len(row) != len(self.header):
                raise RuntimeError("LengthMismatch")
        self.rows.append(row)
        self.modified = 1
        return retVal

    def UpdateRow(self, columnName, row):
        self.modified = 1
        # Same as add but replace existing row.
        raise RuntimeError("NotImplementedYet")

    def FindMatchingRow(self, columnName, matchValue, caseInsensitive=0):
        idx = self.header.index(columnName)
        if type(matchValue) is str and caseInsensitive:
            matchValue = matchValue.lower()
        for row in self.rows:
            value = row[idx]
            if type(value) is str and caseInsensitive:
                value = value.lower()
            if value == matchValue:
                return row

    def FindMatchingRows(self, **criteria):
        # for columnName, value in criteria
        # value = function? then evaluate it on
        raise RuntimeError("NotImplementedYet")

    def FilterRows(self, f):
        l = []
        for row in self.rows:
            if f(row):
                l.append(row)
        return l
