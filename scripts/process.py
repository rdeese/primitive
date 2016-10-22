from Queue import Queue
import itertools
import os
import subprocess
import sys
import threading

def makedirs(x):
    try:
        os.makedirs(x)
    except Exception:
        pass

def primitive(i, o, n, a, m, rep):
    makedirs(os.path.split(o)[0])
    args = (i, o, n, a, m, rep)
    cmd = 'primitive -r 256 -bg "#FFFFFF" -i %s -o %s -n %d -a %d -m %d -rep %d' % args
    subprocess.call(cmd, shell=True)

def create_jobs(in_folder, out_folder, n, a, m, rep):
    result = []
    for name in os.listdir(in_folder):
        base, ext = os.path.splitext(name)
        if ext.lower() not in ['.jpg', '.jpeg', '.png']:
            continue
        out_name = 'm%d-n%d-rep%d.png' % (m, n, rep)
        in_path = os.path.join(in_folder, name)
        out_path = os.path.join(out_folder, base, out_name)
        if os.path.exists(out_path):
            continue
        key = (base, n, m)
        args = (in_path, out_path, n, a, m, rep)
        result.append((key, args))
    return result

def worker(jobs, done):
    while True:
        job = jobs.get()
        log(job)
        primitive(*job)
        done.put(True)

def process(in_folder, out_folder, nlist, alist, mlist, replist, nworkers):
    jobs = Queue()
    done = Queue()
    for i in xrange(nworkers):
        t = threading.Thread(target=worker, args=(jobs, done))
        t.setDaemon(True)
        t.start()
    count = 0
    items = []
    for n, a, m, rep in itertools.product(nlist, alist, mlist, replist):
        for item in create_jobs(in_folder, out_folder, n, a, m, rep):
            items.append(item)
    items.sort()
    for _, job in items:
        jobs.put(job)
        count += 1
    for i in xrange(count):
        done.get()

log_lock = threading.Lock()

def log(x):
    with log_lock:
        print x

if __name__ == '__main__':
    args = sys.argv[1:]
    nlist = [50, 100, 150]
    alist = [0]
    mlist = [1, 5, 8]
    replist = [0, 20]
    nworkers = 1
    process(args[0], args[1], nlist, alist, mlist, replist, nworkers)
