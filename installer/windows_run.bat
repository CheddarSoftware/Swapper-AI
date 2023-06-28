@echo off
REM Please set the following commandline arguments to your prefered settings
set COMMANDLINE_ARGS=--execution-provider cuda --frame-processor face_swapper face_enhancer --video-encoder libvpx-vp9

cd /D "%~dp0"

echo "%CD%"| findstr /C:" " >nul && echo This script relies on Miniconda which can not be silently installed under a path with spaces. && goto end

set PATH=%PATH%;%SystemRoot%\system32

@rem config
set INSTALL_DIR=%cd%\installer_files
set CONDA_ROOT_PREFIX=%cd%\installer_files\conda
set INSTALL_ENV_DIR=%cd%\installer_files\env
set MINICONDA_DOWNLOAD_URL=https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe
set FFMPEG_DOWNLOAD_URL=https://github.com/GyanD/codexffmpeg/releases/download/2023-06-21-git-1bcb8a7338/ffmpeg-2023-06-21-git-1bcb8a7338-essentials_build.zip
set INSTALL_FFMPEG_DIR=%cd%\installer_files\ffmpeg
set conda_exists=F

@rem figure out whether git and conda needs to be installed
call "%CONDA_ROOT_PREFIX%\_conda.exe" --version >nul 2>&1
if "%ERRORLEVEL%" EQU "0" set conda_exists=T

@rem (if necessary) install git and conda into a contained environment
@rem download conda
if "%conda_exists%" == "F" (
	echo Downloading Miniconda from %MINICONDA_DOWNLOAD_URL% to %INSTALL_DIR%\miniconda_installer.exe

	mkdir "%INSTALL_DIR%"
	call curl -Lk "%MINICONDA_DOWNLOAD_URL%" > "%INSTALL_DIR%\miniconda_installer.exe" || ( echo. && echo Miniconda failed to download. && goto end )

	echo Installing Miniconda to %CONDA_ROOT_PREFIX%
	start /wait "" "%INSTALL_DIR%\miniconda_installer.exe" /InstallationType=JustMe /NoShortcuts=1 /AddToPath=0 /RegisterPython=0 /NoRegistry=1 /S /D=%CONDA_ROOT_PREFIX%

	@rem test the conda binary
	echo Miniconda version:
	call "%CONDA_ROOT_PREFIX%\_conda.exe" --version || ( echo. && echo Miniconda not found. && goto end )
)

@rem create the installer env
if not exist "%INSTALL_ENV_DIR%" (
  echo Packages to install: %PACKAGES_TO_INSTALL%
  call "%CONDA_ROOT_PREFIX%\_conda.exe" create --no-shortcuts -y -k --prefix "%INSTALL_ENV_DIR%" python=3.10 || ( echo. && echo Conda environment creation failed. && goto end )
)

if not exist "%INSTALL_FFMPEG_DIR%" (
	echo Downloading ffmpeg from %FFMPEG_DOWNLOAD_URL% to %INSTALL_DIR%
 	call curl -Lk "%FFMPEG_DOWNLOAD_URL%" > "%INSTALL_DIR%\ffmpeg.zip" || ( echo. && echo ffmpeg failed to download. && goto end )
	call powershell -command "Expand-Archive -Force '%INSTALL_DIR%\ffmpeg.zip' '%INSTALL_DIR%\'"

	cd "installer_files"
	setlocal EnableExtensions EnableDelayedExpansion

	for /f "tokens=*" %%f in ('dir /s /b /ad "ffmpeg*"') do (
		ren "%%f" "ffmpeg"
	)
	endlocal
	setx PATH "%INSTALL_FFMPEG_DIR%\bin\;%PATH%"
	cd ..
)

@rem check if conda environment was actually created
if not exist "%INSTALL_ENV_DIR%\python.exe" ( echo. && echo ERROR: Conda environment is empty. && goto end )

@rem activate installer env
call "%CONDA_ROOT_PREFIX%\condabin\conda.bat" activate "%INSTALL_ENV_DIR%" || ( echo. && echo Miniconda hook not found. && goto end )

@rem setup installer env
echo Launching Swapper-AI - please edit windows_run.bat to customize commandline arguments
call python installer.py %COMMANDLINE_ARGS%

echo.
echo Done!

:end
pause



