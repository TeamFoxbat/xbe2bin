# xbe2bin
**WARNING: FLASHING EXTRACTED FIRMWARE MAY BRICK YOUR CHIP. YOU HAVE BEEN WARNED.**

xbe2bin is a Python script intended for extracting STM32 firmware binaries from Xbox Executables (XBE). It is specifically configured for extracting XboxHD+ firmware from the XboxHD+ app but could easily be reconfigured for other applications if necessary.

Currently, it does the following:
 - Pulls latest release from XboxHD+ app on GitHub (or alternatively uses a local .xbe file)
 - Verifies that the .xbe file is actually an XBE
 - Finds the STM32 firmware binary based on a known preamble and verifies that it matches a known pattern and length
 - Checks for known strings for extra validation
 - Displays version number of firmware (if not already available from GitHub release tag name)
 - Displays md5sum of firmware binary
 - Saves extracted firmware binary to new file

# Syntax

Pull latest from GitHub release page:
`python xbe2bin.py`

Use local file instead:
`python xbe2bin.py firmware.xbe`
