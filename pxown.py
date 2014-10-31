import sys
import argparse
import pxssh
from threading import Thread, Lock
from time import sleep

un = "rc3bob"
pw = "netsys"

def worker(IP, commands, lock):
    tries = 0
    while (tries != 5):
        try:
            p = pxssh.pxssh()
            p.login(IP, un, pw)
            break
        except Exception, e:
            tries += 1
            sleep(1)
            print("Error {}: {}".format(IP, e))
    print("Connected to {}".format(IP))
    for i in commands:
        p.sendline(i)
        p.prompt()
        print("{}:\n{}".format(IP, p.before))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', help="The target file", action='store', dest='ftargets', default="targets.txt")
    parser.add_argument('-f', help="The commands file", action='store', dest='fcommands', default="commands.txt")
    args = parser.parse_args()

    targets = []
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

    print(targets)
    threads = []
    lock = Lock()
    for target in targets:
        t = Thread(target=worker, args=(target, commands, lock))
        t.start()
        threads.append(t)
        #sleep(.25)
    for t in threads:
        t.join()

    return 0

if __name__ == '__main__':
    sys.exit(main())
