tmas.py - Tell Me A Story
A choose-your-own-adventure story telling bot

Copyright (C) 2016  Brent.Englehart@gmail.com

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program.  If not, see <http://www.gnu.org/licenses/>.


General Information:

This application will process JSON files containing story elements, to be played back to end users.  General features of the system are that it will allow authors to define replacement fields that they can use within their story to name items or record other user input; allow authors to prompt end users with choices that will define where they go in the story; allow end users to save their progress before a choice is made; allow end users to control the reading speed for the story; and others that are detailed within this document.

File Descriptions:

tmas.py - the main python file containing the story classes used for controlling playback and user interation.
tmasconfig.json - the configuration file for tmas.py.  
game.py - the application wrapper used to handling wen interactions through Flask.
messengerapp.py - the messaging platform class used for controlling interactions between particular messenger app APIs and the Story Telling Bot class
messengerappconfig.json - the configuration file for the application wrapper.
requirements.txt - python requirements file
LICENSE - GNU General Public Licence V3 file
Readme.txt - This file.


Directories:

stories - contains the list of all the author created story JSON files for the application.


Full description - tmasconfig.json 

This file is a standard JSON file containing the configuration fields required by the application.  This is a mandatory file as the system will not function without it.  While some are technical not absolutely required for a working system, it is recommended to leave all fields in place in the file.  Authors should validate this JSON file before use, otherwise the system may not work.

Field Descriptions:

{
	"menugreeting": "Hi.  Welcome to\n\rTell Me A Story\n\r", 
	--the initial message send to the user upon first connection or after quitting the application.

	"menumessage": --the menu presented to the that will allow them to select a story.
	{
		"message": "Which story would you like to play?",    --the message presented to the user.
		"responses":[
		    {
				"response": "The Orchid Of Enduring Beauty", --what the user will see on each button label.
				"filename": "OrchidOfEnduringBeauty.json"    --the file name of the json file within the stories directory.
			},
	        {
				"response": "Becareful What You Wish For",
				"filename": "BecarefulWhatYouWishFor.json"
			}
		]
	},

	"firststep": 100,
	--the ID of the first step in the story JSON file that will be presented to the user.
	
	"notloadedmessage": "Sorry, that story is not quite ready yet.  Try again later.\n\r", 
	--the message presented to the user if the story JSON file cannot be loaded for some reason
	
	"loadedmessage": "OK!  Let's go on an adventure!\n\rAnd remember, you can restart at any time by saying \"#Restart\".  To quit, just say \"#Quit\".\n\rTo save your progress, just say \"#Save\".\n\rTo set the reading speed, say \"#ReadSpeed [number]\". Example: \"#ReadSpeed 5\" will allow 5 seconds to read each message before the next one is sent.\n\rNow lets go!\n\r",
	--the message present to the user when the select a successfully loaded story JSON.

	"cancelmessage": "Returning you to your story.\n\r", 
	--the message sent to the user when they cancel a system command

	"errormessage": "I'm sorry, I encountered an error.\n\r", 
	--a general error message used throughout the system

	"unknownresponse": "Unknown response.  Maybe try clicking a button instead?\n\r", 
	--the message sent to the user when they give a response that the system doesn't know how to handle.

	"readspeedcode": "#ReadSpeed", 
	--the system command that allows the user to select their reading speed.  Example usage:  #Readspeed 5

	"readspeed": 4,	 
	--the default value for the reading speed, in seconds between messages.

	"readspeedupdatemessage" : "Updating reading speed.", 
	--confirmation message sent to the user when the reading speed is successfully changed.

	"readspeederrormessage": "Sorry, but the reading speed must be a number between 1 and 30", 
	--error message given to the user when they send a value that is out of range.

	"savecode": "#Save", 
	--the system command that allows users to save their progress within the story.

	"savemessage": "Progress saved!  To return to this point, just say \"#GoBack\".\n\r",
	--confirmation message sent to the user when the save point is successfully stored.

	"gotocode": "#GoBack", --the system command that allows users to return to their save point.  Defaults to the value of "firststep".
	"gotomessage":         --the menu presented to the user that allows them to confirm they want to return to their save point.
	{
		"message": "Are you sure you want to return to the last save point?", --the message presented to the user
		"responses":[

			--Example container of a response that will cancel out of the question
		    {
				"response": "Keep going.",
				"answer": 0
			},		

			--Example container of a response that will confirm that the user wants to execute the action.
	        {
				"response": "I want to go back.", --what the user will see on each button label.
				"answer": 1,					  --the flag field used by the system to determine the user's answer.  Valid values are 1 for True, 0 for False.
				"extramessage": "Got it.\n\r"     --confirmation message sent to the user for a positive answer.
			}
		]
	},

	"restartcode": "#Restart", --system command that allows the user to restart the story back to the first step.
 	"restartmessage":          --the menu presented to the user that allows them to confirm they want to restart the story.
	{
	 	"message": "Are you sure you want to restart? Your progress will be lost.", 
	 	"responses" :[
		    {
				"response": "Keep going.",
				"answer": 0
			},
		    {
				"response": "Take me back to the start.",
				"answer": 1,
				"nextstep": 3,                    --the step ID within the story JSON file that points the appropriate confirmation step
				"extramessage": "Got it.\n\r"
			},			
	        {
				"response": "I want a new story.", 
				"answer": 1,                       
				"nextstep": 1,	               
				"extramessage": "Got it.\n\r"      
			}
		]
	},

	"quitcode": "#Quit", --system command that allows the user to quit the story.
	"quitmessage":       --the menu presented to the user that allows them to confirm they want to quit the story.
	{
    	"message": "Are you sure you want to quit? Your progress will be lost.", 
    	"responses": [
		    {
				"response": "Keep going.",
				"answer": 0
			},		
	        {
				"response": "I want to quit.", 
				"answer": 1,                   
				"nextstep": 0,                 
				"extramessage": "Got it.\n\r"  
			}
		]
	},

	"devgotocode": "#DevGoto", 
	--the system code that will allow authors to test different steps within the story.  DO NOT ADVERTISE TO GENERAL USERS.  No real harm can be done by this command, but it would allow the users to peak into places they shouldn't see.  Usage within the system:  #DevGoto 600 [devgotopasscode] 

	"devgotopasscode": "beefy",	
	--the passcode to confirm the user is an author.  DO NOT ADVERTISE TO GENERAL USERS.

	"devgotomessage" : "Setting next step.\n\r", 
	--confirmation message sent to the user when the next step requested is successfully found.

	"storiesdir": "stories", 
	--directory within the base folder that holds all of the story JSON files.

	"logfile": "StoryPlayer.log", 
	--log file for the system.  Will roll over every 24 hours.

	"loglevel": "INFO" 
	--Logging level for the system.  Value values are DEBUG, INFO, WARN, ERROR, CRITICAL.
}



Full description - messengerappconfig.json 

This file is a standard JSON file containing the configuration fields required by the messenging platform application wrapper.  This is a mandatory file as the system will not function without it.  This program is currently a work in progress.

Field Descriptions:

{
	"user": "myuser",
	--user name of the messaging platform
	
	"apikey": "a123456-7890-1234-567890123456", 
	--api key for the messaging platform
	
	"webhook": "https://webhookwebsite/incoming",
	--webhook site hosting this application that the messaging platform will send responses to
	
	"unknownresponsemessage": "Sorry, but I really don't know what to do with this response.",
	--generic unknown response error
	
	"gamename": "Adventure Fantasy Quest Time",
	--general game name

	"logfile": "game.log",
	--log file name

	"loglevel": "DEBUG"
	--logging level
}



Full description - StoryJSON.json 

This file is a standard JSON file containing the fields required by the system in order to play a story.  At least one story file must be present, otherwise the system will essentially be 3 general messages that keep repeating whenever a user sends a message.  Authors should validate this JSON file before use, otherwise the system may not work.

Authors can create the stories one step at a time, allowing the author the chance to either receive text input from the user, or give the user preset choices to select from that will direct where they go to next within the story.  Authors can also create steps that will simply display it's message and move onto the next step.

Message text can be broken up by inserting \n whenever the author wants a line break.  The messengerapp.py program is designed to break messages into separate parts wherever it find \n, and send each part to the user with a calculated delay based on the reading speed value.

See the stories folder for a valid example file to start with.

Flags and flag values used by the system to denote different response type:

ENDRESPONSE = 0 --used to end the story and quit from the application.
STARTRESPONSE = 1 --used to confirm restarting the story and moving back to the first step, as denoted within the tmasconfig.json file.
MULTIRESPONSE = 2 --used to give the user diffent choices, with a different next step for each choice.
TEXTRESPONSE = 3 --used to allow the auther to receive text input from the user.  Denoted field and response will be stored by the system, allowing the author to use the field name throughout the story which will be replaced with the user's answer at runtime.
NORESPONSE = 4 --used to allow the author to present a message to the user, then automatically move to the next step.
GOTORESPONSE = 5 --used to confirm returning the user to the save point.
MENURESPONSE = 6 --used to confirm returning users to the main menu.

Field Descriptions:

{
    "step": [

        --Example ENDRESPONSE container.
        {
            "id":  0, --step ID number.
            "message": "OK, bye for now!  To restart again, just say Hi.", --message presented to the user
            "responsetype":  0, --ENDRESPONSE response type value
            "nextstep": 100 --denotes the next step that the system will process.
        },

        --Example MENURESPONSE container.
        {
           "id":  1,
           "message": "Returning to main menu...", 
           "responsetype":  6 --MENURESPONSE response type value
        },

        --Example GOTORESPONSE container.
        {
           "id":  2, 
           "message": "Returning to last save point...", 
           "responsetype":  5 --GOTORESPONSE response type value
        },

        --Example STARTRESPONSE container.
        {
           "id":  3, 
           "message": "Restarting the story...",
           "responsetype":  1, --STARTRESPONSE response type value
           "nextstep": 100
        },

        --Example TEXTRESPONSE container.
        {
           "id":  100,
           "message": "What's your name?",
           "responsetype":  3, --TEXTRESPONSE response type value
           "responsefield": "$ourHero", --field name that will be stored along with the user response.  This field name can be used within the story messages, where it will automatically be replaced with user's response when it encountered in subsequent steps.
	       "nextstep": 101
        },

        --Example MULTIRESPONSE container.
        {
            "id":  101,
            "message": "\"Are you sure that your name is $ourHero?\"",
            "responsetype":  2, --MULTIRESPONSE response type value
            "responses": [
                {
                    "response": "Yes, that's definitely my name", --what the user will see on each button label.
                    "nextstep": 102                               --the next step that will be processed if the user selects this choice.
                },
                {
                    "response": "No, sorry, I mis-spoke.",
                    "nextstep": 100
                }
            ]
        },

        --Example of a MULTIRESPONSE container that will split the story into 2 possible streams of responses.
        {
            "id":  102,
            "message": "Do you like that name?",
            "responsetype":  2, 
            "responses": [
                {
                    "response": "Yes, it's a great name!", 
                    "nextstep": 200                               
                },
                {
                    "response": "No, my parents didn't like my very much.",
                    "nextstep": 300
                }
            ]
        },

        --Example NORESPONSE container.
        {
            "id": 200,
            "message": "Great to hear.",
            "responsetype":  4, --NORESPONSE response type value
            "nextstep": 900
        },

        {
            "id": 300,
            "message": "That's a shame.",
            "responsetype":  4,
            "nextstep": 900
        },

        --Example of a message with line break.
        {
            "id": 900,
            "message": "Well it was nice meeting you.\nHave a nice day.",
            "responsetype":  4,
            "nextstep": 999
        },

        --Example of an end of story MULTIRESPONSE question.
        {
            "id":  999,
            "message": "That was fun. Want to try again?",
            "responsetype":  2,
            "responses": [
                {
                    "response": "I want to restart.",
                    "nextstep": 3
                },
                {
                    "response": "I want to go back to my last save point.",
                    "nextstep": 2
                },                
                {
                    "response": "I want a new story.",
                    "nextstep": 1
                },                 
                {
                    "response": "I've had enough for now.",
                    "nextstep": 0
                }
            ]
        }  
    ]
}
