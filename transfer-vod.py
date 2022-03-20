#!/usr/bin/python2.7

import os
import subprocess
import logging
import time

# Enverioment Variables
INPUT_VOD = ''
OUTPUT_VOD = ''
ARIA2 = '/usr/bin/aria2c'
CDN = ''

TRANSFER_LOG = 'transfer.log'

logging.basicConfig(filename=TRANSFER_LOG, level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

def main():
    ''' Get list of file MOC NFS share '''
    for filename in os.listdir(INPUT_VOD):
        ''' Check if the input file exist in OUTPUT '''
        if os.path.isfile(os.path.join(OUTPUT_VOD, filename)):
            input_file_size = os.stat(os.path.join(INPUT_VOD, filename)).st_size
            output_file_size = os.stat(os.path.join(OUTPUT_VOD, filename)).st_size
            ''' Compare the file size to detect with the download still in process '''
            if input_file_size == output_file_size:
                logging.info(filename + ' are ready to transcode')
                logging.info(filename + ' will be removed from ' + INPUT_VOD)
                os.remove(os.path.join(INPUT_VOD, filename))
                logging.info(filename + ' has removed from ' + INPUT_VOD)
            else:
                logging.info(filename + ' still downloading...')
        else:
            logging.info(filename + ' aria2 started download')
            subprocess.Popen([ARIA2, '--check-certificate=false','--file-allocation=none','--dir=' + OUTPUT_VOD, CDN + filename], close_fds=True)
        

if __name__ == '__main__':
    main()