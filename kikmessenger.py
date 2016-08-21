##############################################################################
##
## kikmessenger.py - Messaging application wrapper used to control interaction
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

import multiprocessing as mp
import time
import json
import logging
import sys
import os

from tmas import StoryController

from kik import KikApi, Configuration
from kik.messages import messages_from_json, TextMessage, SuggestedResponseKeyboard, TextResponse, StartChattingMessage, PictureMessage, LinkMessage, ScanDataMessage, StickerMessage, FriendPickerMessage, UnknownMessage

HTTPFORBIDDEN = 403
HTTPNOTFOUND = 404
HTTPOK = 200


#Multiprocess worker function
#Send the package of messages to the Kik servers.
def sendMessages(args) :
    
    #print 'sendMessages called.'
    #Send each message, with a delay between each
    #There appears to be a bug in the Kik API that may send messages out of order.
    #Unfortunately, there's no real way to handle this here.
    kik = args[0]
    package = args[1]
    storyReadSpeed = args[2]
    delay = args[3]

    try :
        time.sleep(delay)

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
            apiRes = kik.send_messages(responseMessage)
            time.sleep(readSpeed)
    except :
        print 'Unexpected error sending messages: {0} - {1}'.format(sys.exc_info()[0], sys.exc_info()[1])
        pass

#KikMessenger class - used to control interaction between the Kik API and the Story Controller.
# This class processes all requests sent by the Kik messaging platform.
# Used by the MesAppManager class.
class KikMessenger(object) :
    def __init__(self, logger, apiuser = '', apikey = '', webhook = '', name = '', unknownresponsemessage = ''):
        self.name = name

        if unknownresponsemessage :
        	self.unknownresponsemessage = unknownresponsemessage
        else :
        	self.unknownresponsemessage = 'Sorry, but I am unsure of how to handle this response.'

        self.apiuser = apiuser
        self.apikey = apikey
        self.webhook = webhook

        self.logger = logger
        self.kik = None
        self.lastMessage = ''

        self.initKik()

        self.storyController = StoryController(self.name)

        self.sentMessageCount = {}

        self.logger.debug('KikMessenger Class initialized')


    #Create an instance of the Kik API, if not already created.
    def initKik(self) :
    	self.logger.debug('initKik called.')

        if not self.kik :
            try : 
                if (self.apiuser or self.apikey) :
                    self.kik = KikApi(self.apiuser, self.apikey)
                else :
                    self.logger.error('Cannot connect to KiK.  Invalid user name of API key in config and environment variable not set.')
                

                if self.kik and self.webhook :
                    self.kik.set_configuration(Configuration(webhook=self.webhook))
                else :
                    self.kik = None
                    self.logger.error('Cannot connect to KiK.  Invalid webhook in config and environment variable not set.')

            except :
                self.kik = None
                self.logger.error('Cannot connect to KiK: {0} - {1}'.format(sys.exc_info()[0], sys.exc_info()[1]))


    #TCC
    #Check the number of messages to this specific user in the last 30 seconds.
    def checkSentMessageCount(self, chatid, timestamp) :
        self.logger.debug('checkSentMessageCount called.')
        
        messageCount = 0

        try :
            if self.sentMessageCount.has_key(chatid) :
                for messageTime, count in self.sentMessageCount[chatid].items() :
                    if timestamp - messageTime > 30 :
                        del self.sentMessageCount[chatid][messageTime]
                    else :
                        messageCount = messageCount + count
                    self.logger.debug('Time stamp difference: {0}'.format(str(timestamp - messageTime)))
        except :
            self.logger.warn('Unexpected error checking message count: {0} - {1}'.format(sys.exc_info()[0], sys.exc_info()[1]))

        if not self.sentMessageCount.has_key(chatid):
            self.sentMessageCount[chatid] = {}

        self.logger.debug('Message Count: {0}'.format(str(messageCount)))

        #Check if more that 20 messages have been sent in the last 30 seconds.
        if messageCount < 20 :
            #Messages can be freely sent
            return True
        else :
            #Too many messages sent.  You may want to wait 10 seconds before sending more.
            return False


    #Main function call for the class
    #Validate the request, and send the messages for processing.
    def getResponse(self, request) :
    	self.logger.debug('getKikResponse called.')

        if not self.kik :
            return HTTPFORBIDDEN
        
        if not self.kik.verify_signature(request.headers.get('X-Kik-Signature'), request.get_data()):
            return HTTPFORBIDDEN

        #message received by the user
        messages = messages_from_json(request.json['messages'])
        
        try :
            self.processResponse(messages)
        except :
            self.logger.warn('Unexpected error: {0} - {1}'.format(sys.exc_info()[0], sys.exc_info()[1]))

        return HTTPOK


    #Process the messages sent from the messaging platform.
    #TODO - figure out how to enable multiprocessing on this function.
    def processResponse(self, messages) :
         #The list of messages to send
        package = []

        #print '\nReceived user message: ' + message.body + '\n'
        resData = []
        
        for message in messages :
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
                res.body = self.unknownresponsemessage
                package.append(res)

            lastReponse = ''

            if len(resData) > 0:
                for response in resData:
                    #if the current response matches the last response, ignore it to prevent flooding.
                    if not response['message'] == lastReponse :
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
            delay = 0

            #Check the number of messages that have been sent to this chat ID in the last 30 seconds.
            if not self.checkSentMessageCount(message.chat_id, time.time()) :
                self.logger.info('Too Many messages sent.  Waiting 10 seconds.  User: {0}'.format(message.from_user))
                delay = 10

            try :
                #Create a processing pool for sending the responses, to avoid blocking other 
                #kik messages from being processed for an extended period.
                self.logger.debug('Creating processing pool.')
                pool = mp.Pool()
                pool.map_async(sendMessages, [[self.kik, package, storyReadSpeed, delay]])
                pool.close()
            except :
                self.logger.warn('Unexpected error: {0} - {1}'.format(sys.exc_info()[0], sys.exc_info()[1]))

            self.logger.info('Number of packages sent: {0}'.format(str(len(package))))
            self.sentMessageCount[message.chat_id][int(time.time())] = len(package)