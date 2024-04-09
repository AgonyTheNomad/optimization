@echo off
setlocal enabledelayedexpansion

:: Get the number of logical processors on the system
for /f "tokens=*" %%f in ('WMIC CPU Get NumberOfLogicalProcessors /Format:List') do (
    set /a proc=%%f
)

:: Calculate half of the number of processors
set /a workers=proc/2

:: Start Hyperopt workers
for /l %%i in (1,1,%workers%) do (
    start "Worker %%i" cmd /c hyperopt-mongo-worker --mongo=localhost:27017/hyperopt_db --poll-interval=10
)

echo Started %workers% Hyperopt workers.
