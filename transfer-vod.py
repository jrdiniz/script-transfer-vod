#!/usr/bin/python

import os
import subprocess
import logging
import argparse
import gzip
import sqlite3
from datetime import datetime, timedelta

# Environment Variables
INPUT_VOD = "/tmp/test/input"
OUTPUT_VOD = "/tmp/test/output"
WGET = "/usr/bin/wget"
CDN = "http://parc-media01-corpstreaming-tna-mia.terra.com/test/progressive/"

# Log parameters
TIMESTAMP = datetime.today().strftime("%d-%m-%Y")
TRANSFER_LOG = "transfer_" + TIMESTAMP + ".log"
logging.basicConfig(
    filename=TRANSFER_LOG,
    filemode="a",
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - [%(levelname)s] - %(message)s",
)

# Allowed extensions file
ALLOWED_EXTENSIONS = [".mp4", ".mov", ".wmv", ".avi", ".mkv", ".m4a", ".m4v"]

# SQLite Database
DB = sqlite3.connect("transfe-vod.db")


def main():
    parser = argparse.ArgumentParser(description="======= Transfer VOD - v0.2 =======")

    """ Option: --download """
    parser.add_argument(
        "-d",
        "--download",
        action="store_true",
        help="download file from remote location",
    )

    """ Option: --rotate-log """
    parser.add_argument(
        "-r",
        "--rotate-log",
        action="store_true",
        help="compress, rotate and remove old logfiles.",
    )

    """ Get all args """
    args = parser.parse_args()

    if args.download:
        download()
    elif args.rotate_log:
        rotate_logs()


def download():

    """Initialize Database"""
    init_db()

    """Get list of file MOC NFS share"""
    for filename in os.listdir(INPUT_VOD):
        """Check if the input file exist in OUTPUT"""
        if os.path.isfile(os.path.join(OUTPUT_VOD, filename)):
            input_file_size = os.stat(os.path.join(INPUT_VOD, filename)).st_size
            output_file_size = os.stat(os.path.join(OUTPUT_VOD, filename)).st_size
            """ Compare the file size to detect with the download still in progress """
            if input_file_size == output_file_size:
                logging.info(filename + " are ready to transcode")
                logging.info(filename + " will be removed from " + INPUT_VOD)
                os.remove(os.path.join(INPUT_VOD, filename))
                logging.info(filename + " has removed from " + INPUT_VOD)
            else:
                logging.info(filename + " still downloading...")
        else:
            filename_extension = os.path.splitext(filename)[1].lower()
            if filename_extension in ALLOWED_EXTENSIONS:
                logging.info(filename + " wget started download")
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
                logging.warning(
                    filename
                    + " bad filename formatation, will be process at next cronjob."
                )
                os.rename(
                    os.path.join(INPUT_VOD, filename),
                    os.path.join(INPUT_VOD, os.path.splitext(filename)[0]),
                )
            else:
                logging.error(filename + " extension its not supported")


def rotate_logs():
    yesterday = datetime.today() - timedelta(days=1)
    yesterday = yesterday.strftime("%d-%m-%Y")

    """ Get the yesterday log """
    yesterday_log = "transfer_" + yesterday + ".log"
    if os.path.isfile(yesterday_log):
        log = open(yesterday_log, "rb")
        logging.info(yesterday_log + " compress the yesterday log")
        compress = gzip.open(yesterday_log + ".gz", "wb")
        compress.writelines(log)
        compress.close()
        log.close()
        logging.info(yesterday_log + " remove uncompress log")
        os.remove(yesterday_log)


def init_db():
    cursor = DB.cursor()

    # Create database if not exist
    logging.info('Create database and job table')
    cursor.execute(
        """ CREATE TABLE IF NOT EXISTS jobs 
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    filename TEXT NOT NULL,  
                    upload DATETIME, 
                    download DATETIME, 
                    transcode DATETIME, 
                    finished DATETIME
                )"""
    )

    # Commit changes
    DB.commit()

    # Close Databases
    cursor.close()


if __name__ == "__main__":
    main()
