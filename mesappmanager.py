##############################################################################
##
## messengerapp.py - Messaging application wrapper used to control interaction
## various messenger applications and the main Story Telling Bot application.
##
## Copyright (C) 2016  Brent.Englehart@gmail.com
## 
## All references to particular messanging applications are for interacting 
## with their respective API code.  This application claims no ownership
## over any messaging application or APIs.
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License
## as published by the Free Software Foundation; either version 3
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.
##
##############################################################################

import time
import json
import logging
import logging.handlers
import sys
import os

from kikmessenger import KikMessenger

HTTPERROR = 500
HTTPFORBIDDEN = 403
HTTPNOTFOUND = 404
HTTPOK = 200

#MesAppManager class - used to control interaction between the web and individual messaging platforms.
# This class processes all requests sent from the webhook.
class MesAppManager(object) :
    def __init__(self, name = ''):
        self.name = name
       
        self.logger = None

        self._config = {}
        
        self.loadConfig()

        self.initLogging()

        self.messengerApps = {}

        self.initMessengers()

        self.logger.debug('MsgAppManager class initialized.')


    def initLogging(self) :
        try :
            self.logger = logging.getLogger(__name__)
            handler = logging.handlers.TimedRotatingFileHandler(self._config['logfile'], when='midnight',backupCount=5)
            formatter = logging.Formatter('%(asctime)s|p%(process)s|%(filename)s|ln %(lineno)4s|%(levelname)8s|%(message)s','%m-%d %H:%M:%S')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

            if self._config['loglevel'] == 'DEBUG' :
                self.logger.setLevel(logging.DEBUG)
            elif self._config['loglevel'] == 'INFO' :
                self.logger.setLevel(logging.INFO)
            elif self._config['loglevel'] == 'WARN' :
                self.logger.setLevel(logging.WARN)
            elif self._config['loglevel'] == 'ERROR' :
                self.logger.setLevel(logging.ERROR)
            elif self._config['loglevel'] == 'DEBUG' :
                self.logger.setLevel(logging.CRITICAL)
            else :
                self.logger.setLevel(logging.DEBUG)
                self.logger.debug('Unknown logging level.  Defaulting to DEBUG.')

        except:
            print 'Unexpected error: {0} - {1}'.format(sys.exc_info()[0], sys.exc_info()[1])        

    #Load the configuration file for the system
    def loadConfig(self) : 
        #check if the config file has been loaded already by checking the initial message field.
        if not self._config.has_key('gamename') :
            try :
                with open('mesappmanagerconfig.json') as data_file:    
                    self._config = json.load(data_file)
                data_file.close
            except:
                print 'Unexpected error loading config: {0} - {1}'.format(sys.exc_info()[0], sys.exc_info()[1])

    #Initialize the avilable messenger services
    def initMessengers(self) :
        self.logger.debug('MsgAppManager initMessengers called.')
        
        if self._config.has_key('kikmessenger') :
            user = ''
            apikey = ''
            webhook = ''

            if os.environ.get('KIK_USER') and os.environ.get('KIK_API_KEY') and os.environ.get('WEBHOOK'):
                user = os.environ['KIK_USER']
                apikey = os.environ['KIK_API_KEY']
                webhook = os.environ['WEBHOOK']
            else :
                user = self._config['kikuser']
                apikey = self._config['kikapikey']
                webhook = self._config['webhook']


            if (user and apikey and webhook) :
                self.messengerApps['Kik'] = KikMessenger(self.logger, user, apikey, webhook, self._config['gamename'], self._config['unknownresponsemessage'])
            else :
                self.logger.warn('Kik user, API key, or webhook not set.')


    #Main function for the class.
    #Receive the requests from the web, determine the platform, and send the request off for processing.
    def processRequest(self, request) :
        self.logger.debug('processResponse called.')

    	if request.headers.get('X-Kik-Signature') and self.messengerApps.has_key('Kik') :
            return self.messengerApps['Kik'].getResponse(request)
        else :
            return HTTPFORBIDDEN
