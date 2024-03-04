'''
File: xbe2bin.py
Author: TeamFoxbat

Syntax:
Pulls latest from `git_url`
    python xbe2bin.py

Uses local file:
    python xbe2bin.py firmware.xbe
'''

import glob
import hashlib
import json
import sys
import tempfile
import urllib.request
import zipfile

# Known filenames, strings, and offsets
xbe_filename = 'firmware.xbe'
git_url = "https://api.github.com/repos/MakeMHz/xbox-hd-plus-app/releases/latest"
stm32_pre = b'\x64\x44\x00\x00\x00\x20\x00\x20'
stm32_pre_offset = 0x4
stm32_length = 0xD000
known_string1 = 'ENCODER_CONEXANT'
known_string2 = '0123456789abcdef'
ver_offset_ks2 = 0xD7

# use an XBE as a param instead of downloading from github
if len(sys.argv) > 1:
    print("Reading xbe from file")
    xbe_file = sys.argv[1]
    xbe_bytes = bytes(open(xbe_file,'rb').read())
    tag_name = ''

# pull the latest release from github, extract, and find the right file
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
        xbe_file = glob.glob(temp_dir+'/**/' + xbe_filename, recursive=True)[0]
        xbe_bytes = bytes(open(xbe_file,'rb').read())
    except urllib.error.HTTPError as err:
        print("HTTP Error: ",err)
    except Exception as err:
        print(f"unexpected {err=}, {type(err)=}")
        raise
    print("Done")
    xbe_bytes = bytes(open(xbe_file,'rb').read())

# verify that this file really is an XBE
if (xbe_bytes[0:4] == 'XBEH'.encode()):
    print("File appears to be valid OG Xbox Executable")
    
    # find the begining of the STM32 binary using the preamble.
    # this could break in the future. the correct preamble is 
    # 0x00200020 but this is not unique enough to search on its own
    bin_start = xbe_bytes.find(stm32_pre) + stm32_pre_offset
    bin_stop = bin_start + stm32_length
    
    # check if ending of binary is a bunch of ones
    if (xbe_bytes[bin_stop-0xff:bin_stop] == b''.ljust(0xff, b'\xff')):
        obfs = False
        print("Found STM32 binary preamble!")
        bin_bytes = xbe_bytes[bin_start:bin_stop]
        
        # Look for a known string to make sure it's not obfuscated
        if bin_bytes.find(known_string1.encode()):
            print("Strings look valid!")
        else:
            print("WARNING: Binary may be obfuscated...this might not work")
        
        # try to get firmware version from the binary.
        # this sometimes appears to be wrong on some versions.
        ver_idx = bin_bytes.find(known_string2.encode()) + ver_offset_ks2
        ver_str = 'v' + str(bin_bytes[ver_idx]) + '.' + str(bin_bytes[ver_idx+1]) + '.' + str(bin_bytes[ver_idx+2])
        print("Release Version (from firmware): " + ver_str)
        print("Release Version (from Github): " + tag_name)
        print("MD5SUM: " + hashlib.md5(bin_bytes).hexdigest())
        # dump the bytes to a new file
        tag_name = ver_str if tag_name == '' else tag_name
        with open("./firmware_"+tag_name+".bin", 'wb') as bin_file:
            bin_file.write(bin_bytes)
        print("firmware_"+tag_name+".bin")
    else:
        print("ERROR: Length of STM32 may be truncated. Does not appear to be 0xD000 bytes long.")
else:
    print("ERROR: " + sys.argv[1] + " does not appear to be valid Xbox Executable")
