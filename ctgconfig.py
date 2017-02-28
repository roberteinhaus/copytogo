import argparse
import ConfigParser
import logging
import os
import sys

import const

'''
Created on 28.02.2017

@author: Robert Einhaus
'''


class CTGConfig(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.config = self.load_config()
        self.parse_arguments()
        self.check_config()

    def get(self, section, value):
        return self.config.get(section, value)

    def getboolean(self, section, value):
        return self.config.getboolean(section, value)

    def load_config(self):
        configfile = const.CONF_PATH + os.sep + const.CONF_FILE
        config = ConfigParser.SafeConfigParser(
            {
                'dir': '',
                'loglevel': str(logging.WARNING),
            }
        )
        config.read(configfile)
        return config

    def parse_arguments(self):
        parser = argparse.ArgumentParser(
            description='Copy music to your USB stick'
        )
        parser.add_argument('--verbose', '-v', action='count',
                            help="verbosity level (-v infos, -vv debug)"
                            )
        parser.add_argument('--version', action='version',
                            version='CopyToGo v%s' % const.COPYTOGO_VERSION
                            )
        args = parser.parse_args()

        if args.verbose == 1:
            self.config.set('COPYTOGO', 'loglevel', str(logging.INFO))
        elif args.verbose >= 2:
            self.config.set('COPYTOGO', 'loglevel', str(logging.DEBUG))

        logfile = const.LOG_PATH + os.sep + const.LOG_FILE
        logging.basicConfig(filename=logfile,
                            level=self.config.getint('COPYTOGO', 'loglevel'),
                            format='%(asctime)s | %(levelname)s: %(message)s',
                            datefmt='%d.%m.%Y %H:%M:%S'
                            )
        logging.addLevelName(99, "LOG")

    def check_config(self):
        if (self.config.has_option('COPYTOGO', 'default_config') and
                self.config.getboolean('COPYTOGO', 'default_config')):
            logging.critical(
                'Default config found, please edit your config - exiting!')
            print('Default config found, please edit your config - exiting!')
            sys.exit(1)
        if (self.config.get('AUDIO', 'dir') == ""):
            logging.critical("audio directory not set - exiting!")
            sys.exit(1)
