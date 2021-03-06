from __future__ import with_statement

from ConfigParser import RawConfigParser
import sys
import urllib2
import urllib
import cookielib
from BeautifulSoup import BeautifulSoup

def send_sms( message, target = None, config = "gulesider.cfg", verbose = False, dry = False, single_message = True, record_output = True ):
    cfg = RawConfigParser()
    cfg.read( config )
    username = cfg.get( "login", "username" )
    password = cfg.get( "login", "password" )
    useragent = cfg.get( "client", "agent" )
    using_default = target == None
    if using_default:
        target = cfg.get( "phone", "target" )
    if verbose:
        print >>sys.stderr, "[send_sms] Message:", message
        print >>sys.stderr, "[send_sms] Target:", target
        print >>sys.stderr, "[send_sms] Username:", username
        print >>sys.stderr, "[send_sms] Password:", "*" * len(password)
        print >>sys.stderr, "[send_sms] User-Agent:", useragent
        print >>sys.stderr, "[send_sms] Dry run?", dry
    max_message_len = 145 if single_message else 444
    if len(message) > max_message_len:
        dots = 2
        message = message[:max_message_len-dots] + "." * dots
        if verbose:
            print >>sys.stderr, "[send_sms] Message too long (limit %d), shortening." % max_message_len
            print >>sys.stderr, "[send_sms] Shortened message:", message
    url_base = "https://www.gulesider.no/mypage/"
    login_url = url_base + "login.c"
    login_postdata = urllib.urlencode( (("username", username), ("password", password)) )
    headers = {}
    cookie_jar = cookielib.LWPCookieJar()
    opener = urllib2.build_opener( urllib2.HTTPCookieProcessor( cookie_jar ) )
    if useragent:
        headers["User-Agent"] = useragent
    if verbose:
        print >>sys.stderr, "[send_sms] Logging in.."
    login_req = urllib2.Request( login_url, login_postdata, headers )
    login_flo = opener.open( login_req )
    login_data = login_flo.read()
    soup = BeautifulSoup( login_data )
    if record_output:
        with open( "gulesider.login.response.html", "w" ) as f:
            print >> f, soup.prettify()
    if verbose:
        navn = soup.find( "p", "oppfnavn" ).string.strip()
        print >> sys.stderr, "[send_sms] Connected as:", navn
        for index, cookie in enumerate( cookie_jar ):
            print >> sys.stderr, "[send_sms] Cookie #%d:" % index, cookie
    login_flo.close()
    status_url = url_base + "sendSmsInline.c"
    status_req = urllib2.Request( status_url, data = None, headers = headers )
    status_flo = opener.open( status_req )
    status_data = status_flo.read()
    soup = BeautifulSoup( status_data )
    if record_output:
        with open( "gulesider.status.response.html", "w" ) as f:
            print >> f, soup.prettify()
    status_flo.close()
    if dry:
        print >>sys.stderr, "[send_sms] Dry run, aborting."
        return
    send_url = url_base + "sendSmsInline.c"
    sender="tlf.no"
    send_postdata = urllib.urlencode( (("recipients", target), ("text", message),("sender",sender)) )
    send_req = urllib2.Request( status_url, data = send_postdata, headers = headers )
    send_flo = opener.open( send_req )
    send_data = send_flo.read()
    soup = BeautifulSoup( send_data )
    if record_output:
        with open( "gulesider.send.response.html", "w" ) as f:
            print >> f, soup.prettify()
    send_flo.close()

if __name__ == '__main__':
    dry = "real" not in sys.argv
    send_sms( "Hello world [test message to self].", verbose = True, dry = dry )
