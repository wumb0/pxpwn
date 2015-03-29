#!/usr/bin/env python
import sys
import argparse
import pxssh
from threading import Thread, Lock
from time import sleep, strftime

def worker(IP, commands, un, pw, lock, quiet, outfile, diff):
    for tries in range(1,3): #try to connect twice
        try:
            p = pxssh.pxssh()
            p.login(IP, un, pw, login_timeout=3)
            break
        except Exception, e:
            err = str(e).split('\n')[0] #take error message
            if "password".upper() in err.upper(): #invalid password
                if not quiet: print("Error {}: {}".format(IP, err))
                return -1
            if "could not set shell prompt".upper() in err.upper() or "EOF" in err.upper(): #for some reason this means connection refused
                if not quiet: print("Error {}: {}".format(IP, "Connection Refused"))
                if (tries == 2):
                    return -1
            sleep(.5)
            if tries == 2: #max tries exceeded
                if not quiet: print("Error {}: {}".format(IP, err))
                return -1
    if not p.isalive(): return -1 #if the shell is dead then exit
    print("Connected to {}".format(IP))
    output = []
    for i in commands: #send each command
        if not p.isalive(): return -1
        p.sendline(i)
        p.prompt()
        output.append(p.before)
    p.logout()
    if quiet: return 0
    if (diff): #write to different files
        with open(IP + ".out", "a+") as file:
            file.write(strftime("%c"))
            file.write('\n')
            for o in output:
                file.write(o.replace(chr(13), ""))
                file.write('\n')
    else: #write to same file
        lock.acquire() #make sure one thread at a time writes
        if outfile:
            with open(outfile, "a+") as file:
                file.write("{} {}:\n".format(IP, strftime("%c")))
                file.write('\n')
                for o in output:
                    file.write(o.replace(chr(13), "")) #get rid of carriage returns
                    file.write('\n')
        else:
            print("{}:\n".format(IP))
            for o in output:
                print(o)
        lock.release()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', help="The target file", action='store', dest='ftargets', default="targets.txt")
    parser.add_argument('-f', help="The commands file", action='store', dest='fcommands', default="commands.txt")
    parser.add_argument('-u', help='The username to login with', action='store', dest='uname', default='root')
    parser.add_argument('-p', help='The password to log in with', action='store', dest='passwd', default='changeme')
    parser.add_argument('-o', help='The output file, defaults to stdout', action='store', dest='outfile' )
    parser.add_argument('-q', help='do not produce command output', action='store_true', dest='quiet')
    parser.add_argument('-d', help="different files for each IP... negates -o option", action='store_true', dest='diff')
    args = parser.parse_args()

    quiet = args.quiet
    outfile = args.outfile
    targets = []
    diff = args.diff
    try:
        with open(args.ftargets, 'r') as f: #get targets
            targets = f.read().split('\n')
    except:
        print("Cannot open file {}".format(args.ftarget))
    targets = [ i for i in targets if i != '']

    commands = []
    try:
        with open(args.fcommands, 'r') as f: #get commands
            commands = f.read().split('\n')
    except:
        print("Cannot open file {}".format(args.fcommands))
        return -1
    commands = [i for i in commands if i != ''] #cut out blank lines

    threads = []
    lock = Lock()
    for target in targets: #fire the lasers (asynchronously)
        t = Thread(target=worker, args=(target, commands, args.uname, args.passwd, lock, quiet, outfile, diff))
        t.start()
        threads.append(t)
    for t in threads: #wait for each thread to finish before exiting
        t.join()

    return 0

if __name__ == '__main__':
    sys.exit(main())
