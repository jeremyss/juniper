#!/usr/bin/python
import datetime
import argparse
import getpass
import pexpect

_author__ = "Jeremy Scholz"

parser = argparse.ArgumentParser(description='Remote networking device command processor')
parser.add_argument('-v', action='store_true', help='Output results to terminal')
parser.add_argument('-host', type=str, help='Host(s) to run command on, separate multiple hosts with comma')
parser.add_argument('-command', type=str,
                    help='Command(s) to run enclosed in \'\', separate multiple commands with comma')
args = parser.parse_args()

command = []
hostList = []
exCommands = []
commands = ''
hosts = ''

def _run_command(command, results, lineHost, session):
    output = str()
    prompt = session.before
    promptnew = prompt.split('\n')
    prompt = str(promptnew[-1])
    output += '\n******************************\n' + 'Host -> ' + lineHost.strip() \
              + '\n' + 'Command -> ' + command + '\n\n'

    session.sendline(command)
    session.expect(prompt + r'> $', timeout=120)
    output += session.before
    '''
    for lineOutput in stdout:
        output += lineOutput
    '''
    if args.v:
        print output
    results.write(output)


now = datetime.datetime.now()
currentDate = now.strftime('%m-%d-%Y')
currentTime = now.strftime('%H-%M-%S')

timestamp = currentDate + "-" + currentTime
filesSaved = []

username = raw_input("Enter your username: ")
password = getpass.getpass("Enter your password: ")

if not args.command:
    commands = raw_input("Enter commands list filename: ")
if not args.host:
    hosts = raw_input("Enter hosts filename: ")

print "Username: %s" % username
if args.command:
    print "Input commands: %s" % args.command
else:
    print "Input commands file: %s" % commands
if args.host:
    print "Host list: %s" % args.host
else:
    print "Host file: %s" % hosts
runScript = raw_input("script will run with the above configuration... procede? Y/N: ")
runScript = str.lower(runScript)

if runScript == "y":
    # read commands into list
    if args.command:
        exCommands = args.command.split(',')
    else:
        try:
            commandsFile = open(commands, 'r')
            exCommands = commandsFile.readlines()
            exCommands = map(lambda s: s.strip(), exCommands)
            commandsFile.close()
        except IOError:
            print "ERROR::File not found %s" % commands
            exit(0)

    # read hosts into list
    if args.host:
        hostList = args.host.split(',')
    else:
        try:
            hostsFile = open(hosts, 'r')
            hostList = hostsFile.readlines()
            hostsFile.close()
        except IOError:
            print "ERROR::File not found %s" % hosts
            exit(0)

    for lineHost in hostList:
        print "Running commands for %s...please wait" % lineHost.strip()
        try:
            session = pexpect.spawn(
                "ssh -l " + username + " -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o PubkeyAuthentication=no "
                + lineHost.strip(), timeout=3, maxread=65535)
            session.expect('.*assword.')
            session.sendline(password)
            session.expect(r'> $')
        except:
            print "Unable to connect to %s" % lineHost
            continue

        filesSaved.append(lineHost.strip() + "-" + timestamp)
        results = open(lineHost.strip() + "-" + timestamp, 'w')
        session.sendline("set cli screen-length 0")
        session.expect(r'> $')
        for lineCommand in exCommands:
            _run_command(lineCommand, results, lineHost, session)
        session.sendline("exit")
        output = '\n******************************\n***********complete***********\n******************************\n'
        if args.v:
            print output
        results.write(output)
        results.close()

    if len(hostList) > 1:
        print "\nFiles saved to\n"
    else:
        print "\nFile saved to\n"
    for i in filesSaved:
        print i
else:
    exit(0)
