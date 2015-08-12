#!/usr/bin/python
# -*- coding:utf-8 -*-

from __future__ import with_statement, print_function
import os
import re

from datetime import datetime

from trello import TrelloClient, Unauthorized, ResourceUnavailable

# Application Configuration Section
APPLICATION_CONFIGURATION_SUPPORTER_ENABLED = False

virtenv = os.environ['OPENSHIFT_PYTHON_DIR'] + '/virtenv/'
virtualenv = os.path.join(virtenv, 'bin/activate_this.py')
try:
    execfile(virtualenv, dict(__file__=virtualenv))
except IOError:
    pass
#
# IMPORTANT: Put any additional includes below this line.  If placed above this
# line, it's possible required libraries won't be in your searchable path
#

def get_cardid_by_memberid(cards):
    cardid_by_memberid = {}

    for card in cards:
        for member_id in card.member_ids:
            if member_id not in cardid_by_memberid.keys():
                cardid_by_memberid[member_id] = set()

            cardid_by_memberid[member_id].add(card.id)

    return cardid_by_memberid

def application(environ, start_response):

    ctype = 'text/plain'
    if environ['PATH_INFO'] == '/health':
        response_body = "1"
    elif environ['PATH_INFO'] == '/env':
        response_body = ['%s: %s' % (key, value)
                    for key, value in sorted(environ.items())]
        response_body = '\n'.join(response_body)
    else:
        ctype = 'text/html'
        response_body = '''<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Systems Engineering current assignments</title>
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap.min.css">
        <!-- HTML5 shim and Respond.js for IE8 support of HTML5 elements and media queries -->
        <!-- WARNING: Respond.js doesn't work if you view the page via file:// -->
        <!--[if lt IE 9]>
            <script src="https://oss.maxcdn.com/html5shiv/3.7.2/html5shiv.min.js"></script>
            <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
        <![endif]-->
        <style>
@import url("https://fonts.googleapis.com/css?family=Source+Sans+Pro:300,400,700");
html {
  font-family: sans-serif;
  -ms-text-size-adjust: 100%;
  -webkit-text-size-adjust: 100%;
}
body {
  font-family: "Source Sans Pro", Calibri, Candara, Arial, sans-serif;
  font-size: 15px;
  line-height: 1.42857143;
  color: #333333;
  background-color: #ffffff;
  padding: 30px;
}
        </style>
    </head>
    <body>'''

        trello = TrelloClient(os.environ['TRELLO_API_KEY'], token=os.environ['TRELLO_TOKEN'])

        # lets get all the boards goern can read and filter out the Sys-Eng board
        for board in trello.list_boards():
            if board.name == 'Systems Engineering Projects and Status':
                syseng_board = board

        # now, get a list of WIP cards
        for list in syseng_board.all_lists():
            if list.name == 'Work In Progress (Committed)':
                wip_cards = list.list_cards()

        cardid_by_memberid = get_cardid_by_memberid(wip_cards)

        response_body += """<h1>Systems Engineering current assignments</h1>"""

        for member in syseng_board.get_members():
            num_cards = 0

            try:
                num_cards = len(cardid_by_memberid[member.id])
            except:
                pass

            response_body += """<div class="row"><div class="col-md-12"><h2>%s <span class="badge">%s</span> (%s)</h2>""" % (member.full_name, num_cards, member.username)

            # lets print all cards one of us is working on
            for card in wip_cards:
                if member.id in card.member_ids:
                    card_name = card.name

                    response_body += '<p>'

                    for label in card.labels:
                        if label.name == 'Issues':
                            response_body += '<span class="label label-warning">&nbsp;</span>'
                        elif label.name == 'Blocked':
                            response_body += '<span class="label label-danger">&nbsp;</span>'
                        else:
                            response_body += '<span class="label label-success">&nbsp;</span>'

                    if card_name.find("[%s]" % (member.username)) != -1:
                        response_body += """%s<span class="label label-primary">owner</span>&nbsp;""" % (re.sub('\[[%s]*\]' % (member.username), '', card_name))

                        card.fetch()
                        if card.due != '':
                            response_body += "due: %s" % (card.due.encode('utf-8'))
                    else:
                        response_body += "%s" % (card_name)

                    if APPLICATION_CONFIGURATION_SUPPORTER_ENABLED == True:
                        if (card.id in cardid_by_memberid[member.id]) and (card_name.find("[%s]" % (member.username)) == -1):
                            response_body += """&nbsp;<span class="label label-default">supporter</span>"""

                    response_body += '</p>'

            response_body += '</div></div><!-- row -->'

        response_body += '''<!-- container -->
<!-- jQuery (necessary for Bootstrap's JavaScript plugins) -->
<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>
<!-- Include all compiled plugins (below), or include individual files as needed -->
<script src="js/bootstrap.min.js"></script>
</body>
</html>'''

    status = '200 OK'
    response_headers = [('Content-Type', ctype), ('Content-Length', str(len(response_body)))]
    #
    start_response(status, response_headers)
    return [response_body]

#
# Below for testing only
#
if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    httpd = make_server('localhost', 8051, application)
    # Wait for a single request, serve it and quit.
    httpd.handle_request()
