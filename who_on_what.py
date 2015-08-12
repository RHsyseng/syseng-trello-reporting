#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import with_statement, print_function
import os
import re
from datetime import datetime

from trello import TrelloClient, Unauthorized, ResourceUnavailable

from jinja2 import Environment, PackageLoader

HTML_START = """
<!DOCTYPE html>
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
}
   </style>
  </head>
  <body role="document">
    <div class="container" role="main">
    <h1>Systems Engineering current assignments</h1>"""

HTML_END = """
    </div><!-- container -->
    <!-- jQuery (necessary for Bootstrap's JavaScript plugins) -->
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>
    <!-- Include all compiled plugins (below), or include individual files as needed -->
    <script src="js/bootstrap.min.js"></script>
  </body>
</html>"""

if __name__ == "__main__":
    trello = TrelloClient(os.environ['TRELLO_API_KEY'], token=os.environ['TRELLO_TOKEN'])
#    tmplt_env = Environment(loader=PackageLoader('syseng', 'templates'))

    # lets get all the boards goern can read and filter out the Sys-Eng board
    for board in trello.list_boards():
        if board.name == 'Systems Engineering Projects and Status':
            syseng_board = board

    # now, get a list of WIP cards
    for list in syseng_board.all_lists():
        if list.name == 'Work In Progress (Committed)':
            wip_cards = list.list_cards()

    print(HTML_START)

    for member in syseng_board.get_members():
        print("""<div class="row"><div class="col-md-12"><h2>%s (%s)</h2>""" % (member.full_name, member.username))

        # lets print all cards one of us is working on
        for card in wip_cards:
            if member.id in card.member_ids:
                card_name = card.name

                print('<p>')

                for label in card.labels:
                    if label.name == 'Issues':
                        print('<span class="label label-warning">&nbsp;</span>')
                    elif label.name == 'Blocked':
                        print('<span class="label label-danger">&nbsp;</span>')
                    else:
                        print('<span class="label label-success">&nbsp;</span>')

                if card_name.find("[%s]" % (member.username)) != -1:
                    print("""%s<span class="label label-info">owner</span>""" % (re.sub('\[[%s]*\]' % (member.username), '', card_name)))
                else:
                    print("%s" % (card_name))

                print('</p>')

        print('</div></div><!-- row -->') # task

    print(HTML_END)
#    who_on_what_template = tmplt_env.get_template('who_on_what.html.j2')
#    print(who_on_what_template.render(members=syseng_board.get_members(), cards=wip_cards))
