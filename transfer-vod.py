#!/usr/bin/python
import os
import argparse
import subprocess
import logging
from datetime import datetime

# Environment Variables
INPUT_VOD = {
        'standard': '/mnt/corpstreaming/transcode/sem_logo/hd/',
        'webstory': '/mnt/corpstreaming/transcode/sem_logo/webstory/',
        'vertical': '/mnt/corpstreaming/transcode/sem_logo/vertical/'
    }
OUTPUT_VOD = {
        'standard': '/mnt/ftp/transcode/sem_logo/hd/',
        'webstory': '/mnt/ftp/transcode/sem_logo/webstory/',
        'vertical': '/mnt/ftp/transcode/sem_logo/vertical/'
    }
WGET = "/usr/bin/wget"
RSYNC = "/usr/bin/rsync"
CDN = {
        'direct':'https://media-corpstreaming.terra.com.br/',
        'akamai':'https://transcode-transfer.akamaized.net/',
        'cloudflare':'https://vod.gorobei.net/'      
    }
    
# Log parameters
TIMESTAMP = datetime.today().strftime("%d-%m-%Y")
TRANSFER_LOG = '/dados/scripts/log/transfer_' + TIMESTAMP + ".log"
logging.basicConfig(filename=TRANSFER_LOG, filemode="a", level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Log object
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Log Formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - [%(levelname)s] - %(message)s")

# Allowed extensions file
ALLOWED_EXTENSIONS = [".mp4", ".mov", ".wmv", ".avi", ".mkv", ".m4a", ".m4v"]


def main():
    parser = argparse.ArgumentParser(description="Transfer VOD files script - v0.2")
    parser.add_argument('--debug', action='store_true', default=False, help="Debug mode to detect transfer problems.")
    parser.add_argument('--cdn', default='direct', help='Which CDN you want to use to download the VODs (akamai, cloudflare or direct)')
    parser.add_argument('--profile', default="standard", help="Which PROFILE you want transcode (standard, webstory, vertical)")
    parser.add_argument('--type', help="The VODs will be transfer by private or public network (private, public)")
    args = parser.parse_args()
    if args.debug:
        debugger()
    else: 
        if args.type.lower() == 'public':
            ''' Create CDN full path '''
            cdn_path = CDN[args.cdn] + INPUT_VOD[args.profile].split('/',3)[3]
            download(
                cdn=cdn_path,
                input_vod=INPUT_VOD[args.profile],
                output_vod=OUTPUT_VOD[args.profile],
                profile=args.profile
            )
        elif args.type.lower() == 'private':
            sync_file(
                input_vod=INPUT_VOD[args.profile],
                output_vod=OUTPUT_VOD[args.profile]
            )
            
    
def download(cdn, input_vod, output_vod, profile):

    """Get list of file MOC NFS share"""
    for filename in os.listdir(input_vod):
        """Check if the input file exist in OUTPUT"""
        if os.path.isfile(os.path.join(output_vod, filename)):
            input_file_size = os.stat(os.path.join(input_vod, filename)).st_size
            output_file_size = os.stat(os.path.join(output_vod, filename)).st_size
            """ Compare the file size to detect with the download still in progress """
            if input_file_size == output_file_size:
                logger.info(filename + " are ready to transcode")
                logger.info(filename + " will be removed from " + input_vod)
                os.remove(os.path.join(input_vod, filename))
                logger.info(filename + " has removed from " + input_vod)
            else:
                logger.info(filename + " still downloading...")
        else:
            filename_extension = os.path.splitext(filename)[1].lower()
            if filename_extension in ALLOWED_EXTENSIONS:
                logger.info('New transfer: CDN - ' + cdn + ' PROFILE - ' + profile)
                logger.info(filename + " wget started download")
                subprocess.Popen(
                    [
                        WGET,
                        "--no-check-certificate",
                        "--tries=100",
                        "--verbose",
                        "--append-output=" + TRANSFER_LOG,
                        "--directory-prefix=" + output_vod,
                        cdn + filename,
                    ],
                    close_fds=True,
                )
            elif filename_extension in [".1", ".2", ".3"]:
                logger.warning(
                    filename
                    + " bad filename formatation, will be process at next cronjob."
                )
                os.rename(
                    os.path.join(input_vod, filename),
                    os.path.join(input_vod, os.path.splitext(filename)[0]),
                )
            else:
                logger.error(filename + " extension its not supported")

def sync_file(input_vod, output_vod):
    """Get list of file MOC NFS share"""
    list_of_files = os.listdir(output_vod)
    sync_running = [sync_file for sync_file in list_of_files if sync_file.startswith('.') and sync_file != '.__watch_folder_persist_state']
    if sync_running:
        logger.info('Its not possible to sync another files because the file ' + sync_running[0] + ' still in syncing process.')
    else:
        for filename in os.listdir(input_vod):
            logger.info("Start sync file "+ filename + ".")
            subprocess.Popen(
                    [
                        RSYNC,
                        "-Cravzpt",
                        "--remove-source-files",
                        "-azv",
                        input_vod + filename,
                        output_vod + filename
                    ],
                    close_fds=True,
                )
            break

def debugger():
    logger.debug('Transfer debug file')
    print('Direct: ' + CDN['direct'] + 'transcode/test/test.mp4')
    print('Akamai: ' + CDN['akamai'] + 'transcode/test/test.mp4')
    print('Cloudflare: ' + CDN['cloudflare'] + 'transcode/test/test.mp4')
    subprocess.Popen(
        [
            WGET,
            "--no-check-certificate",
            "--tries=10",
            "--verbose",
            "--server-response",
            "--append-output=" + TRANSFER_LOG,
            "--directory-prefix=./",
            CDN['direct'] + 'transcode/test/test.mp4',
        ],
        close_fds=True,
    )

if __name__ == "__main__":
    main()
