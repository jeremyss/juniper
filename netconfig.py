#!/usr/bin/python
import datetime
import argparse
import getpass
import pexpect

_author__ = "Jeremy Scholz"

parser = argparse.ArgumentParser(description='Juniper device configuration command processor')
parser.add_argument('-v', action='store_true', help='Output results to terminal')
parser.add_argument('-host', type=str, help='Host(s) to run command on, separate multiple hosts with comma')
parser.add_argument('-command', type=str,
                    help='Command(s) to run enclosed in \'\', separate multiple commands with comma. \n'
                         'Last command should be \'commit and-quit\' to commit the configuration')
args = parser.parse_args()

command = []
hostList = []
exCommands = []
commands = ''
hosts = ''
validcommands = ["activate", "annotate", "copy", "deactivate", "delete", "insert", "protect", "rename", "replace",
                 "rollback", "save", "set", "show", "status", "top", "unprotect", "wildcard"]

def check_command(validcommands,exCommands):
    if len(exCommands) == 0:
        print "Please specify a command to run\n"
        exit(1)
    else:
        for vc in validcommands:
            if exCommands[0].startswith(vc):
                return True

def _run_command(command, results, lineHost, session, conferror):
    output = str()
    prompt = session.before
    promptnew = prompt.split('\n')
    prompt = str(promptnew[-1])
    output += '\n******************************\n' + 'Host -> ' + lineHost.strip() \
              + '\n' + 'Command -> ' + command + '\n\n'

    session.sendline(command)
    if "commit and-quit" in command:
        session.expect(prompt + r'> $', timeout=120)
        output += session.before
    else:
        session.expect(prompt + r'# $', timeout=120)
        output += session.before
    if ("error" in output) or ("unknown" in output):
        session.sendline('rollback 0')
        output += session.before
        session.expect(prompt + r'# $', timeout=120)
        session.sendline('exit')
        output += session.before
        session.expect(prompt + r'> $', timeout=120)
        output += "\n\nConfiguration error - CONFIGURATION ROLLED BACK\n\n"
        if args.v:
            print output
        results.write(output)
        return "true"
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
    conferror = "false"
    # read commands into list
    if args.command:
        exCommands = args.command.split(',')
        if not check_command(validcommands,exCommands):
            print "Command must begin with one of the following below"
            for vc in validcommands:
                print vc,
            exit(1)
    else:
        try:
            commandsFile = open(commands, 'r')
            exCommands = commandsFile.readlines()
            commandsFile.close()
            if not check_command(validcommands,exCommands):
                print "Command must begin with one of the following below"
                for vc in validcommands:
                    print vc,
                exit(1)
        except IOError:
            print "ERROR::File not found %s" % commands
            exit(1)

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
            session = pexpect.spawn("ssh -l " + username + " -o StrictHostKeyChecking=no " + lineHost.strip(),
                                    timeout=3, maxread=65535)
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
        session.sendline("configure")
        session.expect(r'# $')
        for lineCommand in exCommands:
            conferror = _run_command(lineCommand, results, lineHost, session, conferror)
            if conferror == "true":
                break

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