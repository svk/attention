from optparse import OptionParser
from sys import stderr, stdin, exit
from subprocess import Popen
import re

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option( "-1", "--once", dest="once", default=False, action="store_true", help="trigger only once and then exit" )
    parser.add_option( "-p", "--pattern", dest="patterns", action="append", type="string" )
    parser.add_option( "-i", "--invert", default=False, action="store_true", help="trigger when none of the patterns match" )
    options, args = parser.parse_args()
    regexes = []
    alert_command = args
    def trigger():
        try:
            x = Popen( alert_command )
            x.communicate()
        except:
            print >> stderr, "Exception handled during run of", alert_command
    print >> stderr, "Alert command: ", alert_command
    for regex in options.patterns:
        print >> stderr, "Loading regex: ", regex
        regexes.append( re.compile( regex ) )
    print >> stderr, "Loaded %d pattern(s)." % len(regexes)
    if options.once:
        print >> stderr, "Triggering only once."
    if options.invert:
        print >> stderr, "Triggering on no pattern matched."
    while True:
        line = stdin.readline()
        if line:
            line = line.strip()
            print >> stderr, "Reading line:", line
            matching = any( [ r.match( line ) for r in regexes ] )
            if options.invert:
                matching = not matching
            if matching:
                print >> stderr, "Triggered!"
                trigger()
                if options.once:
                    print >> stderr, "Exiting after trigger."
                    exit(0)

