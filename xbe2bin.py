'''
File: xbe2bin.py
Author: TeamFoxbat

Syntax:
Pulls latest from `git_url`
    python xbe2bin.py

Uses local file:
    python xbe2bin.py upgrade.xbe firmware.xbe
'''

import glob
import hashlib
import json
import sys
import tempfile
import urllib.request
import zipfile

# Known filenames, strings, and offsets
firmware = {'filename': 'firmware.xbe',
            'file': '',
            'bytes': b'',
            'length': 0xD000}
bootloader = {'filename': 'upgrade.xbe',
              'file': '',
              'bytes': b'',
              'length': 0x2800}
concat_bytes = b''
git_url = "https://api.github.com/repos/MakeMHz/xbox-hd-plus-app/releases/latest"
stm32_pre = b'\x64\x44\x00\x00\x00\x20\x00\x20'
stm32_pre_offset = 0x4
known_string1 = 'ENCODER_CONEXANT'
known_string2 = '0123456789abcdef'
ver_offset_ks2 = 0xD7
ver_string = ''
tag_name = ''

# use an XBE as a param instead of downloading from github
if len(sys.argv) == 2:
    print("Reading xbe from file")
    bootloader['file'] = sys.argv[1]
    firmware['file'] = sys.argv[2]

elif len(sys.argv) != 0 and len(sys.argv) != 2:
    print("Syntax:\n\tpython xbe2bin.py\nor\n\tpython xbe2bin.py upgrade.xbe firmware.xbe")
    sys.exit(0)

# pull the latest release from github, extract, and find the right files
else:
    print("Downloading latest from internet...")
    temp_dir_obj = tempfile.TemporaryDirectory()
    temp_dir = temp_dir_obj.name + '/'
    try:
        latest_json = json.loads(urllib.request.urlopen(git_url).read().decode('utf-8'))
        zip_url = latest_json['assets'][0]['browser_download_url']
        tag_name = latest_json['tag_name']
        zip_filepath = temp_dir + zip_url.split('/')[-1]
        urllib.request.urlretrieve(zip_url, zip_filepath)
        with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        firmware['file'] = glob.glob(temp_dir+'/**/' + firmware['filename'], recursive=True)[0]
        bootloader['file'] = glob.glob(temp_dir+'/**/' + bootloader['filename'], recursive=True)[0]
    except urllib.error.HTTPError as err:
        print("HTTP Error: ",err)
        raise
    except Exception as err:
        print(f"unexpected {err=}, {type(err)=}")
        raise
    print("Done")

firmware['bytes'] = bytes(open(firmware['file'],'rb').read())
bootloader['bytes'] = bytes(open(bootloader['file'],'rb').read())

for xbe in [bootloader, firmware]:
    # verify that this file really is an XBE
    if (xbe['bytes'][0:4] == 'XBEH'.encode()):
        print("File appears to be valid OG Xbox Executable")
        
        # find the begining of the STM32 binary using the preamble.
        # this could break in the future. the correct preamble is 
        # 0x00200020 but this is not unique enough to search on its own
        bin_start = xbe['bytes'].find(stm32_pre) + stm32_pre_offset
        bin_stop = bin_start + xbe['length']
        
        # check if ending of binary is a bunch of ones
        if (xbe['bytes'][bin_stop-0xff:bin_stop] == b''.ljust(0xff, b'\xff')):
            print("Found STM32 binary preamble in " + xbe['filename'])
            bin_bytes = xbe['bytes'][bin_start:bin_stop]
            
            # Look for a known string in firmware to make sure it's not obfuscated
            if xbe['length'] == firmware['length']:
                if bin_bytes.find(known_string1.encode()):
                    print("Strings look valid!")
                else:
                    print("WARNING: Binary may be obfuscated...this might not work")
            
                # try to get version from the firmware.
                # this sometimes appears to be wrong on some versions (?)
                ver_idx = bin_bytes.find(known_string2.encode()) + ver_offset_ks2
                ver_str = 'v' + str(bin_bytes[ver_idx]) + '.' + str(bin_bytes[ver_idx+1]) + '.' + str(bin_bytes[ver_idx+2])
                print("Release Version (from firmware): " + ver_str)
                print("Release Version (from Github): " + tag_name)
                tag_name = ver_str if tag_name == '' else tag_name
            # cat the bootloader and firmware together
            concat_bytes = concat_bytes + bin_bytes
        else:
            print("ERROR: Length of STM32 may be truncated. Does not appear to be 0xD000 bytes long.")
            sys.exit(1)
    else:
        print("ERROR: " + xbe['filename'] + " does not appear to be valid Xbox Executable")
        sys.exit(1)

# dump the bytes to a new file
print("firmware_"+tag_name+".bin MD5SUM: " + hashlib.md5(concat_bytes).hexdigest())
with open("./firmware_"+tag_name+".bin", 'wb') as bin_file:
    bin_file.write(concat_bytes)
