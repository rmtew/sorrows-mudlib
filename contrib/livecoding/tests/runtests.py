import sys, os, glob, unittest, StringIO, weakref

# It shouldn't matter which directory this is run in, as long as

def RunTests():
    # Determine whether the file name is an absolute path or not.
    drive, path = os.path.splitdrive(__file__)
    if len(drive):
        # Absolute path to the file.
        filePath = __file__
    else:
        # Relative path to the file, add to the current directory.
        filePath = os.path.join(os.getcwd(), __file__)

    # We now have the directory this file is in.
    dirPath = os.path.dirname(filePath)
    sys.path.append(dirPath)

    # We now have the directory one level up (where livecoding.py is).
    libPath = os.path.split(dirPath)[0]
    sys.path.append(libPath)

    testFilePaths = glob.glob(os.path.join(dirPath, "test_*.py"))

    suite = unittest.TestSuite()

    for idx, testFilePath in enumerate(testFilePaths):
        moduleName = os.path.splitext(os.path.basename(testFilePath))[0]
        module = __import__(moduleName)

        tests = unittest.TestLoader().loadTestsFromModule(module)
        suite.addTest(tests)

    class SIO(StringIO.StringIO):
        def writeline(self, line):
            self.write(line +"\n")

    # There is a lot of printed output in the CodeCompiler.  Hide it.
    oldStdOut = sys.stdout
    sio = sys.stdout = SIO()
    try:
        unittest.TextTestRunner().run(suite)
    finally:
        #sio.seek(0)
        sys.stdout = oldStdOut
        #print sio.getvalue()

if __name__ == '__main__':
    RunTests()
