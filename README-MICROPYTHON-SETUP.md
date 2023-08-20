# Micropython development environment setup

This is about how to set up a working development environment for micropython with VS Code

## Some basic concepts

* Micropython is only needed on the device
* You need a tool to upload your source to the device, like mpremote (see below)
* You need stubs only to take advantage of autocompletion and linting, but not for the actual micropython program to run on the device.

## References

General micropython docs
<https://docs.micropython.org>

General micropython-cli docs
<https://micropy-cli.readthedocs.io/en/latest/>

Mpremote tool
<https://docs.micropython.org/en/latest/reference/mpremote.html>

General micropython download page
<https://micropython.org/download/>

Raspberry pi pico w download page
<https://micropython.org/download/rp2-pico-w/>

Raspberry pi pico "plain/non-w" download page
<https://micropython.org/download/rp2-pico/>

## Install micropython on the device

1. Download the firmware

2. Follow the following instructions found in download page:

> Flashing via UF2 bootloader
>
> To get the board in bootloader mode ready for the
> firmware update, execute machine.bootloader() at the
> MicroPython REPL. Alternatively, hold down the BOOTSEL
> button while plugging the board into USB. The uf2 file
> below should then be copied to the USB mass storage
> device that appears. Once programming of the new
> firmware is complete the device will automatically
> reset and be ready for use.

## Create a virtualenv on development machine

```shell
# Create the virtualenv (once)
python3.11 -m venv myvirtualenv 

# Activate the virtualenv (before using it)
source myvirtualenv/bin/activate
```

## Create a project

```shell
mkdir src
```

Then, write some micropython code in main.py

## Install micropython-cli

Micropython-cli is a tool whose main use is to get and install in current workspace the stubs used to perform autocompletion and syntax check.

Make sure your virtualenv is active

```shell
pip install --upgrade micropy-cli
```

## Search for available stubs, then install (once per device)

Please note: This step creates a folder on user root folder:

```~/.micropy``````

This step must be run once per new device being used, and does not need to be repeated for each new project.

```shell
# Search
micropy stubs search [query]  
micropy stubs search pico  


# Install
micropy stubs add [stub-name]  
micropy stubs add micropython-rp2-pico_w-stubs
```

## Create a new project

This step creates the proper configuration for VS Code to use stubs.

Stubs are needed only for linting and code completion, but not for development.

Settings are created by default under the new project folder; after the project is created, you can do the following (alternative)

* Use the newly created folder as project workspace

* Move the configurations up une level to make the current folder the "project level" (thos makes VS Code read the settings) from withon the current folder.

* Copy the generated configuration from another project, and skip this step.

We follow the second alternative here.

```shell
micropy init dummy
```

Choose the following when prompted:

   Choose any Templates to Generate
      ● VSCode Settings for Autocompletion/Intellisense
      ○ Pymakr Configuration
      ● Pylint MicroPython Settings
      ● Git Ignore Template
      ● main.py & boot.py files

   Which stubs would you like to use?
      ● micropython-rp2-pico-w-stubs
      ● micropython-stdlib-stubs

Bring the following one level up (parallel to the newly created src directory, see above)

* Folder: ```.vscode```
* Folder: ```.micropy```
* File: ```.pylintrc```

Then, remove the ```dummy``` folder (dummy is the newly created project, see above)

## Install mpremote

```shell
pip install mpremote
```

## Basic mpremote usage

```shell

# Connect to device
mpremote

# Reset device (hard reset)
mpremote reset 

# Reset device (soft reset)
mpremote soft-reset

# Run script on device
mpremote run [path/to/local]/main.py  

# Send to device (main.py as main.py on device)
mpremote fs cp main.py :main.py

# Update the copy of utils/driver.py on the device, then execute app.py on the device.
# This is a common development workflow to update a single file and then re-start your program. In this scenario, your main.py on the device would also do import app.
# (example and explainationb copied from docs)

mpremote cp utils/driver.py :utils/driver.py + exec "import app"

# Update the copy of utils/driver.py on the device, then trigger a soft-reset to restart your program, and then monitor the output via the repl command.
# (example and explainationb copied from docs)

mpremote cp utils/driver.py :utils/driver.py + soft-reset repl

# Same as above, but update the entire utils directory first.
# (example and explainationb copied from docs)

mpremote cp -r utils/ :utils/ + soft-reset repl

```
