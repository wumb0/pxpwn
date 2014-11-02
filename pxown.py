import sys
import argparse
import pxssh
from threading import Thread, Lock
from time import sleep

quiet=False
outfile=""
diff=False

def worker(IP, commands, un, pw, lock):
    global outfile
    global quiet
    for tries in range(0,1):
        try:
            print tries
            p = pxssh.pxssh()
            p.login(IP, un, pw, login_timeout=3)
            break
        except Exception, e:
            err = str(e).split('\n')[0]
            if "password".upper() in err.upper():
                print("Error {}: {}".format(IP, err))
                return -1
            if "could not set shell prompt".upper() in err.upper() or "EOF" in err.upper():
                print("Error {}: {}".format(IP, "Connection Refused"))
                if (tries == 2):
                    return -1
            sleep(.5)
            if tries == 2:
                print("Error {}: {}".format(IP, err))
                return -1
    if not p.isalive(): return -1
    print("Connected to {}".format(IP))
    output = []
    for i in commands:
        if not p.isalive(): return -1
        p.sendline(i)
        p.prompt()
        output.append(p.before)
    p.logout()
    if (diff):
        with open(IP + ".out", "a+") as file:
            for o in output:
                file.write(o.rstrip('\n'))
    else:
        lock.acquire()
        if outfile:
            with open(outfile, "a+") as file:
                file.write("{}:\n".format(IP))
                for o in output:
                    file.write(o.rstrip('\r'))
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
    parser.add_argument('-d', help="different files for each IP... negates -o option,", action='store_true', dest='diff')
    args = parser.parse_args()

    global outfile
    global quiet
    global diff
    quiet = args.quiet
    outfile = args.outfile
    targets = []
    diff = args.diff
    try:
        with open(args.ftargets, 'r') as f:
            targets = f.read().split('\n')
    except:
        print("Cannot open file {}".format(args.ftarget))
    targets = [ i for i in targets if i != '']

    commands = []
    try:
        with open(args.fcommands, 'r') as f:
            commands = f.read().split('\n')
    except:
        print("Cannot open file {}".format(args.fcommands))
        return -1
    commands = [i for i in commands if i != '']

    threads = []
    lock = Lock()
    for target in targets:
        t = Thread(target=worker, args=(target, commands, args.uname, args.passwd, lock))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    return 0

if __name__ == '__main__':
    sys.exit(main())
