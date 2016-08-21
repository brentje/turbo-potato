##############################################################################
##
## tmas.py - Tell Me A Story
## A choose-your-own-dventure story telling bot
##
## Copyright (C) 2016  Brent.Englehart@gmail.com
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

import json
import sys
import logging
import os
import copy

reload(sys)
sys.setdefaultencoding('utf-8')

ENDRESPONSE = 0
STARTRESPONSE = 1
MULTIRESPONSE = 2
TEXTRESPONSE = 3
NORESPONSE = 4
GOTORESPONSE = 5
MENURESPONSE = 6

#StoryController class - used to control the StoryPlayer class objects created
# This class monitors all incoming and outgoing messages to each StoryPlayer created,
# and control the creation, user interaction, and destruction of user data. 
#
# Instantiation example: game = StoryController('Adventure Fantasy Time Quest')
# 
# The only recommended function calls are:
#
# - getStoryResponse({Unique user identifier}, {User's text response})
#   This function takes the input from the calling application, and returns the appropriate mesage
#   plus response options if any.  See documentation for more details.
#
#   Return Type: Python list []
#   Return Value: The list of individual dict objects, each containing a message and possibly a list of response options.
#
# - getReadSpeed({Unique user identifier})
#   Optional
#   This function returns the story recommended reading speed rate, in seconds between messages.
#   Calling application does not need to adhere to this rate.  Packages will still contain the complete message
#
#   Return Type: Int
#   Return Value: Reading speed value in seconds
#
# This class requires the 'tmasconfig.json' file in the same directory as this script.
#
class StoryController(object) :
    def __init__(self, name):
        self.name = name
        
        self.logger = None

        # used to store configuration data
        self._config = {}

        #Loaded stories
        self._stories = {}

        #currently running stories
        self.userData = {}

        #list of common responses to pass to the story player
        self.configResponses = {}
        
        self.loadConfig()

        self.initLogging()

        self.logger.debug('StoryController Class initialized.  Name: {0}'.format(name))


    def initLogging(self) :
        try :
            self.logger = logging.getLogger(__name__)
            handler = logging.handlers.TimedRotatingFileHandler(self._config['logfile'], when='midnight', backupCount=5)
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
        if not self._config.has_key('menumessage') :
            try :
                with open('tmasconfig.json') as data_file:    
                    self._config = json.load(data_file)
                data_file.close
            except:
                print 'Unexpected error loading config: {0} - {1}'.format(sys.exc_info()[0], sys.exc_info()[1])        

            self.configResponses['unknownresponse'] = self._config['unknownresponse']
            self.configResponses['invalidresponse'] = self._config['invalidresponse']
            self.configResponses['toolongresponse'] = self._config['toolongresponse']


    #Load the requested story for the user.
    def loadStory(self, storyFilename):
        self.logger.debug('StoryController loadStory storyFilename: {0}'.format(storyFilename))

        if storyFilename :
            if not self._stories.has_key(storyFilename) :
                try :
                    storyFilePath = os.getcwd() + '/' + self._config['storiesdir'] + '/' + storyFilename
                    self.logger.debug('loadStory storyFilename: {0}'.format(storyFilename))
                    with open(storyFilePath) as data_file:    
                        self._stories[storyFilename] = json.load(data_file)
                    data_file.close

                except:
                    self.logger.warn('Unexpected error loading story: {0} - {1}'.format(sys.exc_info()[0], sys.exc_info()[1]))
                    return self._config['notloadedmessage']
        
        self.logger.debug('StoryController loadStory loaded: {0}'.format(storyFilename))                  


    #Present the list of available stories from the config file.
    def presentStories(self, extraMessage = ''):
        self.logger.debug('StoryController presentStories extraMessage: {0}'.format(extraMessage))

        response = {}
        ret = []

        #check if the response if one of the story options.
        #Otherwise, send the initial message and options if no story is loaded.

        if extraMessage :
            #user has already seen the initial greeting.
            response['message'] = extraMessage 
        else :
            response['message'] = self._config['menugreeting'] 

        ret.append(response)

        response = self._config['menumessage']
        ret.append(response)
        
        self.logger.debug('presentStories response: ' + str(response))
        
        return ret


    #Main function for the class.
    #Handles all incoming and outgoing messages from the system.
    #User flags and system commands are checked first before presenting stories or playing a story.
    def getStoryResponse(self, userID, userResponse = '') :
        self.logger.debug('StoryController getStoryResponse userResponse: {0}'.format(userResponse))

        extraMessage = ''

        ret = []

        #Check if there is a currently curring story
        if self.userData.has_key(userID) :

            #Check user flags first

            #Check the Goto flag to see if the current response is for quiting
            if self.userData[userID].userFlags.has_key(self._config['gotocode']) :
                extraMessage = self.checkFlagCommand(userID, userResponse, self._config['gotocode'], self._config['gotomessage']['responses'])
 
                #Check if the Goto flag is still raised
                if self.userData[userID].userFlags.has_key(self._config['gotocode']) :
                    #user didn't answer correctly.  Restate question.
                    self.logger.info('Unknown goto response: {0}'.format(userResponse))
                    extraMessage = self._config['unknownresponse']
                    userResponse = self._config['gotocode'] 

            #Check the Restart flag to see if the current response is for restarting
            elif self.userData[userID].userFlags.has_key(self._config['restartcode']) :
                extraMessage = self.checkFlagCommand(userID, userResponse, self._config['restartcode'], self._config['restartmessage']['responses'])

                #Check if the Restart flag is still raised
                if self.userData.has_key(userID) and self.userData[userID].userFlags.has_key(self._config['restartcode']) :
                    #user didn't answer correctly.  Restate question.
                    self.logger.info('Unknown restart response: {0}'.format(userResponse))
                    extraMessage = self._config['unknownresponse']
                    userResponse = self._config['restartcode'] 

            #Check the Quit flag to see if the current response is for quiting
            elif self.userData[userID].userFlags.has_key(self._config['quitcode']) :
                extraMessage = self.checkFlagCommand(userID, userResponse, self._config['quitcode'], self._config['quitmessage']['responses'])
 
                #Check if the Quit flag is still raised
                if self.userData.has_key(userID) and self.userData[userID].userFlags.has_key(self._config['quitcode']) :
                    #user didn't answer correctly.  Restate question.
                    self.logger.info('Unknown quit response: {0}'.format(userResponse))
                    extraMessage = self._config['unknownresponse']
                    userResponse = self._config['quitcode'] 


            #Check system commands

            #check if dev wants to specify a step number.
            if userResponse.find(self._config['devgotocode'])  == 0:
                extraMessage = self.checkDevGotoCommand(userID, userResponse)
            #check if the user wants to change the reading speed.
            elif userResponse.find(self._config['readspeedcode']) == 0:
                extraMessage = self.checkReadSpeedCommand(userID, userResponse)
            #check if the user wants to save their progress
            elif userResponse == self._config['savecode'] :
                self.userData[userID].saveStep = self.userData[userID].currentStep
                extraMessage = self._config['savemessage']
            #check if the user wants to return to the save point.
            elif userResponse == self._config['gotocode'] :
                self.userData[userID].raiseFlag(self._config['gotocode'])
                ret.append(self._config['gotomessage'])
                return ret
            #check if the user wants to quit
            elif userResponse == self._config['quitcode'] :
                self.userData[userID].raiseFlag(self._config['quitcode'])
                ret.append(self._config['quitmessage'])
                return ret
            #check if the user wants to restart
            elif userResponse == self._config['restartcode'] :
                self.userData[userID].raiseFlag(self._config['restartcode'])
                ret.append(self._config['restartmessage'])
                return ret

        else :
            #No story has been found.  Check response for an option from presentStories
            for option in self._config['menumessage']['responses'] :
                if option['response'] == userResponse :
                    extraMessage = self.loadStory(option['filename'])
                    if not extraMessage :
                        #story has been loaded successfully.  Create user's story object
                        self.logger.debug('Does story exist: {0}'.format(self._stories.has_key(option['filename'])))
                        self.userData[userID] = StoryPlayer(self.name, userID, self._stories[option['filename']], self._config['readspeed'], self._config['firststep'], self.configResponses, self.logger)
                        extraMessage = self._config['loadedmessage']
                        userResponse = ''


        #Check if a story has been started, or if a running story was ended.
        if self.userData.has_key(userID) :
            #Running story found
            ret = self.userData[userID].progressStory(userResponse, extraMessage)

            self.logger.debug('getLastResponseType: {0}'.format(self.userData[userID].lastStep['responsetype']))
            
            #check if the last story step ended the story
            if self.userData[userID].lastStep['responsetype'] == ENDRESPONSE :
                #The user ended the story.  Present the story options
                self.logger.debug('Deleted user data for user: {0}'.format(userID))
                del self.userData[userID]
            #check if the user wants to return to the main menu
            elif self.userData[userID].lastStep['responsetype'] == MENURESPONSE :
                #The user ended the story.  Present the story options
                self.logger.debug('Deleted user data for user: {0}'.format(userID))
                del self.userData[userID]
                ret = ret + self.presentStories()

            return ret

        else :
            #No running story found.  Show the main menu
            return self.presentStories(extraMessage)
    

    #A flag was raised.  Check the response for an appropriate value set the current step if necessary.
    def checkFlagCommand(self, userID, userResponse, flagID, flagResponses) :
        self.logger.debug('StoryController checkGotoCommand userID: userID: {0}  | Response: {1}'.format(userID, userResponse))

        extraMessage = ''

        try :
            for option in flagResponses :
                if option['response'] == userResponse :
                    if option['answer'] :
                        #user opted to return to the specified next step
                        self.userData[userID].currentStep = option['nextstep']
                        extraMessage = option['extramessage']
                    else :
                        #user cancelled
                        extraMessage = self._config['cancelmessage']
        except :
            self.logger.warn('Unexpected error checking flag question: {0} - {1}'.format(sys.exc_info()[0], sys.exc_info()[1]))    
            extraMessage = self._config['errormessage']

        self.userData[userID].lowerFlag(flagID)
        return extraMessage


    #The internal dev goto code was detected.  Check the response for an appropriate value set the current step.
    def checkDevGotoCommand(self, userID, userResponse) :
        self.logger.debug('StoryController checkDevGotoCommand userID: {0}  | Response: {1}'.format(userID, userResponse))

        extraMessage = ''

        try:
            responseParts = userResponse.split(' ', 2)
            if len(responseParts) > 1 :
                if responseParts[1].isdigit() :
                    if  1 <= int(responseParts[1]) <= 100000:
                        if responseParts[2] == self._config['devgotopasscode'] :
                            #user opted to return to the last save point
                            self.logger.debug('Returning to step: {0}'.format(responseParts[1]))
                            self.userData[userID].currentStep = int(responseParts[1])
                            extraMessage = self._config['devgotomessage']
                        else :
                            self.logger.warn('Dev goto invalid passcode. {0} {1}'.format(responseParts[0], responseParts[1]))
                            extraMessage = self._config['unknownresponse']
                    else :
                        self.logger.info('Dev goto response out of range: {0} {1}'.format(responseParts[0], responseParts[1]))
                        extraMessage = self._config['unknownresponse']
                else :
                    self.logger.info('Unknown dev goto response: {0}'.format(responseParts[0], responseParts[1]))
                    extraMessage = self._config['unknownresponse']
            else :
                self.logger.info('Unknown dev goto response: {0}'.format(responseParts[0], responseParts[1]))
                extraMessage = self._config['unknownresponse']
        except :
            self.logger.warn('Unexpected error checking dev goto question: {0} - {1}'.format(sys.exc_info()[0], sys.exc_info()[1]))
            extraMessage = self._config['unknownresponse']

        return extraMessage


    #The read speed code was detected.  Check the response for an appropriate value and set the reading speed.
    def checkReadSpeedCommand(self, userID, userResponse) :
        self.logger.debug('StoryController checkReadSpeedCommand userID: {0}  | Response: {1}'.format(userID, userResponse))

        extraMessage = ''

        try:
            responseParts = userResponse.split(' ', 1)
            if len(responseParts) > 1 :
                if responseParts[1].isdigit() :
                    if  1 <= int(responseParts[1]) <= 30:
                        self.logger.info('Setting read speed: {0}'.format(userResponse))
                        extraMessage = self._config['readspeedupdatemessage'] + ' ' + responseParts[1] + '\n'
                        self.userData[userID].readSpeed = int(responseParts[1])
                    else :
                        self.logger.info('Unknown read spead response: {0}'.format(userResponse))
                        extraMessage = self._config['readspeederrormessage']
                else :
                    self.logger.info('Unknown read spead response: {0}'.format(userResponse))
                    extraMessage = self._config['readspeederrormessage']
            else :
                self.logger.info('Unknown read spead response: {0}'.format(userResponse))
                extraMessage = self._config['readspeederrormessage']
        except :
            self.logger.warn('Unexpected error checking read speed question: {0} - {1}'.format(sys.exc_info()[0], sys.exc_info()[1]))
            extraMessage = self._config['errormessage']

        return extraMessage


    #Get the story recommended reading speed.
    def getReadSpeed(self, userID) :
        self.logger.debug('StoryController getReadSpeed userID: {0}'.format(userID))

        if self.userData.has_key(userID) :
            return self.userData[userID].readSpeed
        else :
            return self._config['readspeed']



#StoryPlayer class - used to control story playback and message creation.
# This class plays through an individual story for a user.
# Used by the StoryController class.  Not recommended to be instantiated alone.
class StoryPlayer(object) :
    def __init__(self, name, userid, currentStory, readSpeed, firstStep, configResponses, logger):
        self.name = name
        self.userid = userid
        self.readSpeed = readSpeed

        self.logger = logger

        # used to store the story data
        self._story = copy.deepcopy(currentStory)

        self.logger.debug('Does story exist: {0}'.format(self._story.has_key('step')))

        # used to store 'unknown response' message
        self.configResponses = copy.deepcopy(configResponses)

        # used to store the default current step.
        self.firstStep = firstStep
        self.currentStep = firstStep
        self.saveStep = firstStep

        self.readSpeed = readSpeed

        # used to store the last step the system processed.
        self.lastStep = {}

        # used to store author defined nouns and object names
        self.userFields = {}

        # used to story flags that the user raised
        self.userFlags = {}

        self.initValues()

        self.logger.debug('StoryPlayer Class initialized.  User: {0}'.format(userid))


    #Initialize all necessary values for the story player to start back at the first step.
    def initValues(self) :
        self.logger.debug('StoryPlayer initValues called.')

        self.lastStep.clear()

        self.lastStep['responsetype'] = STARTRESPONSE
        self.lastStep['nextstep'] = self.firstStep
        self.saveStep = self.firstStep

        self.userFields.clear()
        self.userFlags.clear()

    def raiseFlag(self, flagID) :
        self.userFlags[flagID] = None

    def lowerFlag(self, flagID) :
        self.userFlags.pop(flagID, None)

    #Replace the author defined fields.
    def replaceFields(self, message = ''):
        self.logger.debug('StoryPlayer replaceFields userResponse: {0}'.format(message))

        try :        
            for key, value in self.userFields.items():
                message = message.replace(key, value)
            return message 

        except:
            self.logger.error('Unexpected error: {0} - {1}'.format(sys.exc_info()[0], sys.exc_info()[1]))


    #Main function for the class.
    #Process the user's story response, and provide the next step in the story back.
    def progressStory(self, userResponse = '', extraMessage = ''):
        self.logger.debug('StoryPlayer progressStory userResponse: {0}  | extraMessage: {1}'.format(userResponse, extraMessage))
        self.logger.debug('StoryPlayer progressStory lastStep: {0}'.format(self.lastStep))

        self.logger.debug('Does story exist: {0}'.format(self._story.has_key('step')))

        ret = []

        if extraMessage == '' :
        #As long as there were no extra messages sent, continue the story.
        #Otherwise, the user issued a system command.  Just reload the existing step in that case.
            if self.lastStep['responsetype'] == STARTRESPONSE :
                self.logger.debug('StoryPlayer progressStory STARTRESPONSE')
                #The user is starting the story.  No response expected.
                self.currentStep = self.lastStep['nextstep']

            elif self.lastStep['responsetype'] == NORESPONSE :
                self.logger.debug('StoryPlayer progressStory NORESPONSE')
                #The previous step was a a NORESPONSE step, continue getting steps until something else is found.
                self.currentStep = self.lastStep['nextstep']

            elif self.lastStep['responsetype'] == TEXTRESPONSE :
                self.logger.debug('StoryPlayer progressStory TEXTRESPONSE')
                #The user was asked a freeform question. Story the information.
                if all(x.isalnum() or x.isspace() for x in userResponse):
                    if len(userResponse) <= 30 :
                        self.userFields[self.lastStep['responsefield']] = userResponse
                        self.currentStep = self.lastStep['nextstep']
                    else :
                        extraMessage = self.configResponses['toolongresponse']
                else :
                    extraMessage = self.configResponses['invalidresponse']

            elif self.lastStep['responsetype'] == MULTIRESPONSE :
                self.logger.debug('StoryPlayer progressStory MULTIRESPONSE')
                #The user was asked a multiple choice question.
                testStep = self.currentStep
                for option in self.lastStep['responses'] :
                    if option['response'] == userResponse :
                        self.currentStep = option['nextstep']
                if (testStep == self.currentStep) :
                    #user provided an unknown response.  Repeat current step.
                    self.logger.info('Unknown MULTIRESPONSE response: {0}'.format(userResponse))
                    response = {}
                    response['message'] = self.configResponses['unknownresponse'] 
                    response['responses'] = self.lastStep['responses']
                    ret.append(response)
                    self.logger.info('Unknown MULTIRESPONSE response: {0}'.format(response))
                    return ret

            elif self.lastStep['responsetype'] == GOTORESPONSE :
                self.logger.debug('StoryPlayer progressStory GOTORESPONSE')
                #The user selected to go back to their save point.
                self.currentStep =  self.saveStep

            else :
                #user provided an unknown response.  Repeat current step.
                self.logger.info('Unknown response: {0}'.format(userResponse))
                extraMessage = self.configResponses['unknownresponse'] 

        ret.append(self.getCurrentStep(extraMessage))

        self.logger.debug('progressStory currentStep: {0}'.format(self.currentStep))
        self.logger.debug('progressStory responsetype: {0}'.format(self.lastStep['responsetype']))

        #if this was a Goto response, set the current step to the save point.  Otherwise, just set it to the next scheduled step.
        if self.lastStep['responsetype'] == GOTORESPONSE :
            self.currentStep = self.saveStep
            ret.append(self.getCurrentStep())

        #While the last step retrieved doesn't require any user input, keep getting steps until something else is found.
        while self.lastStep['responsetype'] == NORESPONSE or self.lastStep['responsetype'] == STARTRESPONSE :
            self.currentStep = self.lastStep['nextstep']
            ret.append(self.getCurrentStep())
            
        return ret

    #Find the current step in the story, and update the appropriate data containers
    def getCurrentStep(self, extraMessage = '') :
        self.logger.debug('StoryPlayer getCurrentStep currentStep: {0}  | extraMessage: {1}'.format(self.currentStep, extraMessage))

        foundStep = False        
        ret = {}

        try :
            #Loop through the steps in the story data to find the current step
            for step in self._story.get('step') :
                if step['id'] == self.currentStep :
                    foundStep = True
                    #Deep copy the step referenced from the StoryController class. Otherwise the object reference held in self.lastStep will delete
                    #the StoryController class story object values when the StoryPlayer is deleted.
                    self.lastStep = copy.deepcopy(step)
                    repMessage = self.replaceFields(self.lastStep['message'])
                    ret['message'] = extraMessage + repMessage
                    if self.lastStep.has_key('responses') :
                        ret['responses'] = self.lastStep['responses']
                    break

            if not foundStep :
                self.logger.error('Unable to find step {0}'.format(self.currentStep))
                ret['message'] = self._config['endstoryerrormessage']
                self.initValues()
                self.lastStep['responsetype'] = ENDRESPONSE

        except :
            self.logger.error('Unexpected error finding step {0}. '.format(self.currentStep))
            self.logger.error('Error: {0} - {1}'.format(sys.exc_info()[0], sys.exc_info()[1]))
            ret['message'] = 'I\'m sorry, we\'ve encountered an unexpected error.  Ending story.'
            self.initValues()
            self.lastStep['responsetype'] = ENDRESPONSE
        
        return ret