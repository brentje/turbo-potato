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

from flask import request, Response

from tmas import StoryController

from kik import KikApi, Configuration
from kik.messages import messages_from_json, TextMessage, SuggestedResponseKeyboard, TextResponse, StartChattingMessage, PictureMessage, LinkMessage, ScanDataMessage, StickerMessage, FriendPickerMessage, UnknownMessage

class MessengerApp(object) :
    def __init__(self, name = ''):
        self.name = name
       
        self.logger = None
        
        self._config = {}

        self.kik = None
        
        self.lastMessage = ""


        self.loadConfig()

        self.initLogging()

        self.initKik()

        self.storyController = StoryController(self._config['gamename'])

        self.logger.debug('Class initialized')

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
                with open('messengerappconfig.json') as data_file:    
                    self._config = json.load(data_file)
                data_file.close
            except:
                print 'Unexpected error loading config: {0} - {1}'.format(sys.exc_info()[0], sys.exc_info()[1])        

    def initKik(self) :
    	self.logger.debug('initKik called.')

        try : 
            self.kik = KikApi(self._config['user'], self._config['apikey'])
            self.kik.set_configuration(Configuration(webhook=self._config['webhook']))

        except:
            self.logger.error('Cannot connect to KiK: {0} - {1}'.format(sys.exc_info()[0], sys.exc_info()[1]))
            raise


    def processResponse(self, request) :
    	self.logger.debug('processResponse called.')

        if not self.kik.verify_signature(request.headers.get('X-Kik-Signature'), request.get_data()):
            return Response(status=403)

        #message received by the user
        messages = messages_from_json(request.json['messages'])

         #The list of messages to send
        package = []

        #print '\nReceived user message: ' + message.body + '\n'
        resData = []   
        
        try :
            for message in messages:       
                if isinstance(message, StartChattingMessage) :
                    
                    resData = self.storyController.getStoryResponse(message.chat_id)

                elif isinstance(message, TextMessage) :
                    #There appears to be a bug with the Kik API where it resends the last response from the user.
                    #If one is detected, ignore the message.
                    if not(self.lastMessage == message.body) :
                        resData = self.storyController.getStoryResponse(message.chat_id, message.body)
                        self.lastMessage = message.body

                    #print '\n' + lastMessage + '|' + message.body + '\n'

                elif (isinstance(message, PictureMessage) or isinstance(message, LinkMessage) or isinstance(message, StickerMessage) or isinstance(message, ScanDataMessage) or isinstance(message, FriendPickerMessage)) :
                    #This bot does not really anything with these type, so ignore them.
                    pass

                else : 
                        res = TextMessage()
                        res.to = message.from_user
                        res.chat_id = message.chat_id
                        res.body = self._config('unknownresponsemessage')
                        package.append(res)

                
                if len(resData) > 0:
                    for response in resData:
                        #The story will be return with a \n representing breaks in the message, to allow the user to read each section adequately 
                        resTextSections = response['message'].split('\n')
                    
                        for section in resTextSections :
                            #Check if there is actual text in the section, in case the message ended with \n resulting in a blank section
                            if section :
                                res = TextMessage()
                                res.to = message.from_user
                                res.chat_id = message.chat_id
                                res.body = section
                                package.append(res)

                        #Add the response options, if any, to the last item in the list.
                        if response.has_key('responses') :
                            options = []
                            for option in response['responses'] :
                                options.append(TextResponse(option['response']))

                            package[len(package) - 1].keyboards.append(
                                SuggestedResponseKeyboard(
                                    responses=options
                                )
                            )

                storyReadSpeed = self.storyController.getReadSpeed(message.chat_id)

                #Send each message, with a delay between each
                #There appears to be a bug in the Kik API that may send messages out of order.
                #Unfortunately, there's no real way to handle this here.
                for item in package :
                    #do some reading speed calculations, in order to shorten the time given to short messages.
                    readSpeed = storyReadSpeed
                    #Check if the message is greater than 300 characters.
                    if len(item.body) < 300 :
                        readSpeed = float(readSpeed) * float((float(len(item.body)) / float(300)))
                    if readSpeed < 1 :
                        readSpeed = 1

                    responseMessage = []
                    responseMessage.append(item)
                    self.kik.send_messages(responseMessage)
                    time.sleep(readSpeed)

                    #print '\n Message Sent: ' + item.body + '\n'
        except :
            self.logger.warn('Unexpected error: {0} - {1}'.format(sys.exc_info()[0], sys.exc_info()[1]))

        return Response(status=200)