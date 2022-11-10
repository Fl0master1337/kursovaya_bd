import json
import mysql.connector
import datetime
import logging
from gui import gui
from logging import config


def read_settings():
    with open('credentials.json', 'r') as f:
        settings = json.load(f)
    return settings


def main():
    logname = f'logs/default_{datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d_%H-%M-%S")}.log'
    logging.config.fileConfig('logging.conf', defaults={'logfilename': logname})
    logger = logging.getLogger('ssmLogger')
    settings = read_settings()
    try:
        db = mysql.connector.connect(
            host=settings['hostname'],
            user=settings['username'],
            password=settings['password'],
            database=settings['database']
        )
        cursor = db.cursor()
        gui(db, cursor, logger, settings)
    finally:
        cursor.close()
        db.close()


if __name__ == '__main__':
    main()
