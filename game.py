##############################################################################
##
## game.py - Flask wrapper application, for interacting with various messenger 
##           apps.
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
import sys

from flask import Flask, request, Response

from messengerapp import MessengerApp

app = Flask(__name__)

messengerApp = MessengerApp('Messenger App')

@app.route('/incoming', methods=['GET'])
def verify():

    return Response(response="Hello world", status=200)

@app.route('/incoming', methods=['POST'])
def incoming():

    try :
        return Response(status=messengerApp.processRequest(request))
    except:
        print 'Error: {0} - {1}'.format(sys.exc_info()[0], sys.exc_info()[1])        
        return Response(status=403)

    

if __name__ == '__main__':
    app.run(port=8080, debug=False)


