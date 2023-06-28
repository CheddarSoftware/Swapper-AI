import argparse
import glob
import os
import shutil
import site
import subprocess
import sys


script_dir = os.getcwd()


def run_cmd(cmd, capture_output=False, env=None):
    return subprocess.run(cmd, shell=True, capture_output=capture_output, env=env)


def check_env():
    conda_not_exist = run_cmd("conda", capture_output=True).returncode
    if conda_not_exist:
        print("Conda is not installed. Exiting...")
        sys.exit()
    
    if os.environ["CONDA_DEFAULT_ENV"] == "base":
        print("Create an environment for this project and activate it. Exiting...")
        sys.exit()


def install_dependencies():
    run_cmd("conda install -y -k git")
    run_cmd("git clone https://github.com/CheddarSoftware/Swapper-AI.git")


    update_dependencies()


def update_dependencies():
    global MY_PATH
    
    os.chdir(MY_PATH)

    run_cmd("git fetch --all")
    run_cmd("git reset --hard origin/main")
    run_cmd("git pull")
    run_cmd("python -m pip install -r requirements.txt")


def start_app():
    global MY_PATH
    
    os.chdir(MY_PATH)

    sys.argv.pop(0)
    args = ' '.join(sys.argv)
    print("Launching App")
    run_cmd(f'python run.py {args}')


if __name__ == "__main__":
    global MY_PATH
    
    MY_PATH = "Swapper-AI"

    
    check_env()

    if not os.path.exists(MY_PATH):
        install_dependencies()
    else:
        updatechoice = input("Check for Updates? [y/n]").lower()
        if updatechoice == "y":
           update_dependencies()

    os.chdir(script_dir)
    start_app()
