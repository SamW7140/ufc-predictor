@if "%SCM_TRACE_LEVEL%" NEQ "4" @echo off

:: ----------------------
:: KUDU Deployment Script
:: Version: 1.0.17
:: ----------------------

:: Prerequisites
:: -------------

:: Verify node.js installed
where node 2>nul >nul
IF %ERRORLEVEL% NEQ 0 (
  echo Missing node.js executable, please install node.js, if already installed make sure it can be reached from current environment.
  goto error
)

:: Setup
:: -----

setlocal enabledelayedexpansion

SET ARTIFACTS=%~dp0%..\artifacts

IF NOT DEFINED DEPLOYMENT_SOURCE (
  SET DEPLOYMENT_SOURCE=%~dp0%.
)

IF NOT DEFINED DEPLOYMENT_TARGET (
  SET DEPLOYMENT_TARGET=%ARTIFACTS%\wwwroot
)

IF NOT DEFINED NEXT_MANIFEST_PATH (
  SET NEXT_MANIFEST_PATH=%ARTIFACTS%\manifest

  IF NOT DEFINED PREVIOUS_MANIFEST_PATH (
    SET PREVIOUS_MANIFEST_PATH=%ARTIFACTS%\manifest
  )
)

IF NOT DEFINED KUDU_SYNC_CMD (
  :: Install kudu sync
  echo Installing Kudu Sync
  call npm install kudusync -g --silent
  IF !ERRORLEVEL! NEQ 0 goto error

  :: Locally just running "kuduSync" would also work
  SET KUDU_SYNC_CMD=%appdata%\npm\kuduSync.cmd
)

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: Deployment
:: ----------

echo Handling python deployment.

:: 1. KuduSync
IF /I "%IN_PLACE_DEPLOYMENT%" NEQ "1" (
  call :ExecuteCmd "%KUDU_SYNC_CMD%" -v 50 -f "%DEPLOYMENT_SOURCE%" -t "%DEPLOYMENT_TARGET%" -n "%NEXT_MANIFEST_PATH%" -p "%PREVIOUS_MANIFEST_PATH%" -i ".git;.hg;.deployment;deploy.cmd"
  IF !ERRORLEVEL! NEQ 0 goto error
)

:: 2. Select Python version
call :SelectPythonVersion

:: 3. Create virtual environment
IF NOT EXIST "%DEPLOYMENT_TARGET%\env\azure.env.%PYTHON_RUNTIME%.txt" (
  IF EXIST "%DEPLOYMENT_TARGET%\requirements.txt" (
    echo Creating %PYTHON_RUNTIME% virtual environment.
    call :ExecuteCmd "%PYTHON_EXE%" -m venv "%DEPLOYMENT_TARGET%\env"
    IF !ERRORLEVEL! NEQ 0 goto error

    call :ExecuteCmd "%DEPLOYMENT_TARGET%\env\Scripts\pip.exe" install setuptools
    IF !ERRORLEVEL! NEQ 0 goto error

    call :ExecuteCmd "%DEPLOYMENT_TARGET%\env\Scripts\pip.exe" install -r "%DEPLOYMENT_TARGET%\requirements.txt"
    IF !ERRORLEVEL! NEQ 0 goto error

    REM Add marker file
    echo %PYTHON_RUNTIME%> "%DEPLOYMENT_TARGET%\env\azure.env.%PYTHON_RUNTIME%.txt"
  )
)

goto end

:: Execute command routine that will echo out when error
:ExecuteCmd
setlocal
set _CMD_=%*
call %_CMD_%
if "%ERRORLEVEL%" NEQ "0" echo Failed exitCode=%ERRORLEVEL%, command=%_CMD_%
exit /b %ERRORLEVEL%

:error
endlocal
echo An error has occurred during web site deployment.
call :exitSetErrorLevel
call :exitFromFunction 2>nul

:exitSetErrorLevel
exit /b 1

:exitFromFunction
()

:end
endlocal
echo Finished successfully.

:SelectPythonVersion

IF DEFINED PYTHON_RUNTIME goto :END_SELECT_PYTHON_VERSION

FOR /F "tokens=*" %%i in ('python -c "import sys; print(sys.version)"') do (
    set PYTHON_VERSION=%%i
)

echo %PYTHON_VERSION%

IF NOT DEFINED PYTHON_VERSION (
    echo Python version could not be determined.
    set PYTHON_RUNTIME=python-3.9
) ELSE (
    IF "%PYTHON_VERSION:~0,1%"=="3" (
        set PYTHON_RUNTIME=python-3.9
    ) ELSE (
        echo Unsupported Python version: %PYTHON_VERSION%
        exit /b 1
    )
)

echo Python runtime: %PYTHON_RUNTIME%
set PYTHON_EXE=%SYSTEMDRIVE%\python%PYTHON_RUNTIME:~7,1%%PYTHON_RUNTIME:~9,1%\python.exe

:END_SELECT_PYTHON_VERSION 