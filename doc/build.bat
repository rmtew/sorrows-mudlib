@@echo off

REM Check command line arguments.
if "%1" EQU "html" goto build
if "%1" EQU "htmlhelp" goto build

echo Please specify a documentation build target.
set this=%~n0
echo %this% html
echo %this% htmlhelp

goto end

:build

REM Find the 32 bit Program Files directory.
set PFA=%ProgramFiles%
if not "%ProgramFiles(x86)%" == "" set PFA=%ProgramFiles(x86)%

REM Set defaults for non-existent environment variables.
if "%HTMLHELP%" EQU "" set HTMLHELP=%PFA%\HTML Help Workshop\hhc.exe

REM Hard-coded paths.
set PYTHON=C:\python27\python.exe
set DOCPATH=D:\VCS\SVN\Python\Stackless\__exports__\release27-maint-export\release27-maint\Doc

set TARGETTYPE=%1
set SOURCEPATH=%~dp0%
set BUILDPATH=%SOURCEPATH%build
set DOCTREEPATH=%BUILDPATH%\doctrees
set TARGETPATH=%BUILDPATH%\%TARGETTYPE%

if not exist %BUILDPATH% mkdir %BUILDPATH%
if not exist %DOCTREEPATH% mkdir %DOCTREEPATH%
if not exist %TARGETPATH% mkdir %TARGETPATH%

cmd /C %PYTHON% %DOCPATH%\tools\sphinx-build.py -b%TARGETTYPE% -d%DOCTREEPATH% %SOURCEPATH% %TARGETPATH%

echo %HTMLHELP%
if "%TARGETTYPE%" EQU "htmlhelp" "%HTMLHELP%" %TARGETPATH%\SorrowsMudlib.hhp

:end