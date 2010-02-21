REM Most of the time this will complain about the directory already existing.
2>nul makedir %~dp0%build\html

c:\python26\scripts\sphinx-build %~dp0 %~dp0%build\html
