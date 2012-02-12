from __future__ import with_statement

import re
import sys

from poplib import POP3, POP3_SSL

from ConfigParser import RawConfigParser

class MailFilter:
    def __init__(self, function, sender = None, subject = None):
        self.sender_regex = re.compile( sender ) if sender else None
        self.subject_regex = re.compile( subject ) if subject else None
        self.function = function
        assert sender or subject
    def __call__(self, headers):
        subject = headers["Subject"]
        sender = headers["From"]
        ematch = (not self.sender_regex or self.sender_regex.match( sender ))
        umatch = (not self.subject_regex or self.subject_regex.match( subject ))
        if ematch and umatch:
            self.function( headers )

class MailFilters:
    def __init__(self):
        self.filters = []
    def __call__(self, headers):
        for mfilter in self.filters:
            mfilter( headers )

def pretty_stringify_mail( headers ):
    return "Mail '%s' from '%s'" % (headers["Subject"], headers["From"])

def pretty_print_mail( headers ):
    print pretty_stringify_mail( headers )

sms_sanity_countdown = 10 # must start program again.. can't even successfully send this many messages in 1 day

def gulesider_sms_mail( headers ):
    global sms_sanity_countdown
    from gulesider import send_sms
    message = pretty_stringify_mail( headers )
    if sms_sanity_countdown <= 0:
        print >> sys.stderr, "[gulesider_sms_mail] will not send SMS '%s', too many sent already" % message
    else:
        sms_sanity_countdown -= 1
        print >> sys.stderr, "[gulesider_sms_mail] sending SMS '%s', left until restart required: %d" % (message, sms_sanity_countdown)
        send_sms( message )

def print_mail( headers ):
    subject = headers["Subject"].replace("'", "\"")
    sender = headers["From"].replace("'", "\"")
    date = headers["Date"].replace("'", "\"")
    print "MAIL @'%s' F'%s' S'%s'" % (date, sender, subject)

def parse_headers( lines ):
    # very hacky, avoids multilines
    watched = "From:", "Subject:", "Date:"
    rv = {}
    for line in lines:
        if any( [ line.startswith(x) for x in watched ] ):
            field, data = line.split( ":", 1 )
            rv[field] = data.strip()
    return rv

def check_mail( config, function, delete = True ):
    cfg = RawConfigParser()
    cfg.read( config )
    username = cfg.get( "pop3", "username" )
    password = cfg.get( "pop3", "password" )
    ssl = cfg.get( "pop3", "ssl" ).lower()
    ssl = (ssl == "true") or (ssl == "yes")
    host = cfg.get( "pop3", "host" )
    port = cfg.get( "pop3", "port" )
    conn = (POP3_SSL if ssl else POP3)(host, port)
    conn.user( username )
    conn.pass_( password )
    no_messages, _ = conn.stat()
    for i in range(1, no_messages+1):
        _, headers, _ = conn.top( i, 0 )
        function( parse_headers( headers ) )
    if delete:
        for i in range(1, no_messages+1):
            conn.dele( i )
    conn.quit()

def check_mail_loop( interval, config, function, delete = True, verbose = True ):
    import time
    while True:
        time.sleep( interval )
        if verbose:
            print >> sys.stderr, "[check_mail_loop] checking mail (interval of %f seconds)" % interval
        check_mail( config, function, delete = delete )

def read_filters( filename, verbose = True ):
    blessed = "action", "subject", "sender"
    functions = { "print" : pretty_print_mail, "gulesider-sms" : gulesider_sms_mail }
    kwargs = {}
    rv = []
    with open( filename, "r" ) as f:
        for line in f.readlines():
            line = line.strip()
            if not line:
                continue
            if line == "!":
                rv.append( MailFilter( **kwargs ) )
                if verbose:
                    print >> sys.stderr, "Loaded filter: ", kwargs
                kwargs = {}
            else:
                name, content = line.split( " ", 1 )
                assert name in blessed
                if name == "action":
                    kwargs[ "function" ] = functions[ content ]
                else:
                    kwargs[ name ] = content
    assert len( kwargs.items() ) == 0
    x = MailFilters()
    x.filters = rv
    return x

if __name__ == '__main__':
    config = "forwarded-mail.cfg"
    filterfile = "mailcheck.filters"
    interval = 60 # a minute
    filters = read_filters( filterfile )
    check_mail_loop( interval, config, filters, delete = True )
