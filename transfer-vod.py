#!/usr/bin/python
import os
import subprocess
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

# Environment Variables
INPUT_VOD = '/mnt/corpstreaming/transcode/sem_logo/hd/'
OUTPUT_VOD = '/mnt/ftp/transcode/sem_logo/hd/'
WGET = "/usr/bin/wget"
CDN = 'http://parc-media01-corpstreaming-tna-mia.terra.com/transcode/sem_logo/hd/'

# Log parameters
TIMESTAMP = datetime.today().strftime("%d-%m-%Y")
TRANSFER_LOG = "/dados/scripts/log/transfer.log"

# Log object
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Log Formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - [%(levelname)s] - %(message)s")

# Log Handler
handler = TimedRotatingFileHandler(
    TRANSFER_LOG, when="midnight", backupCount=7, interval=1, encoding="utf-8"
)
handler.suffix = "_%d-%m-%Y"
handler.setFormatter(formatter)
logger.addHandler(handler)

# Allowed extensions file
ALLOWED_EXTENSIONS = [".mp4", ".mov", ".wmv", ".avi", ".mkv", ".m4a", ".m4v"]

def main():

    """Get list of file MOC NFS share"""
    for filename in os.listdir(INPUT_VOD):
        """Check if the input file exist in OUTPUT"""
        if os.path.isfile(os.path.join(OUTPUT_VOD, filename)):
            input_file_size = os.stat(os.path.join(INPUT_VOD, filename)).st_size
            output_file_size = os.stat(os.path.join(OUTPUT_VOD, filename)).st_size
            """ Compare the file size to detect with the download still in progress """
            if input_file_size == output_file_size:
                logger.info(filename + " are ready to transcode")
                logger.info(filename + " will be removed from " + INPUT_VOD)
                os.remove(os.path.join(INPUT_VOD, filename))
                logger.info(filename + " has removed from " + INPUT_VOD)
            else:
                logger.info(filename + " still downloading...")
        else:
            filename_extension = os.path.splitext(filename)[1].lower()
            if filename_extension in ALLOWED_EXTENSIONS:
                logger.info(filename + " wget started download")
                subprocess.Popen(
                    [
                        WGET,
                        "--no-check-certificate",
                        "--tries=100",
                        "--verbose",
                        "--append-output=" + TRANSFER_LOG,
                        "--directory-prefix=" + OUTPUT_VOD,
                        CDN + filename,
                    ],
                    close_fds=True,
                )
            elif filename_extension in [".1", ".2", ".3"]:
                logger.warning(
                    filename
                    + " bad filename formatation, will be process at next cronjob."
                )
                os.rename(
                    os.path.join(INPUT_VOD, filename),
                    os.path.join(INPUT_VOD, os.path.splitext(filename)[0]),
                )
            else:
                logger.error(filename + " extension its not supported")


if __name__ == "__main__":
    main()
