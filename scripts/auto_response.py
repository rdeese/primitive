from Queue import Queue
import os
import requests
import tempfile
import itertools
import random
import threading
import subprocess
import sys

from twython import Twython
from twython import TwythonStreamer

consumer_key = 'qFPPU65i8vHEalWQDrmM61aOz' 
consumer_secret = 'GKExu6pRtGFL9EEWRibcAWNPwU4Ewhphzu53Co2H7zmKDSG5Am' 
access_token = '789981061186920448-34VL5BtNTf7vd1aBNBAfJ5gUSxRS3pV'
access_token_secret = 'HZ3alPBJUxfFAVFTYrw9r1DPuCBKfovwfQER5QrmSxWv2'
account_user_id = '789981061186920448'

twitter = Twython(consumer_key, consumer_secret, access_token, access_token_secret)

def stdout(str):
  sys.stdout.write(str)
  sys.stdout.write("\n")
  sys.stdout.flush()

def primitive(i, o, n, a, m, rep):
    args = (i, o, n, a, m, rep)
    cmd = 'primitive -r 256 -bg "#FFFFFF" -i %s -o %s -n %d -a %d -m %d -rep %d' % args
    stdout("Starting primitive job...")
    stdout(cmd)
    subprocess.call(cmd, shell=True)

def first_media_url(tweet):
  entities = tweet.get("extended_entities")
  if entities:
    media = entities.get("media")
    if type(media) == list:
      media_entry = media[0]
      if media_entry.get("type") == "photo":
        return media_entry.get("media_url")
  return None

def upload_photo(path):
  photo = open(path, 'rb')
  response = twitter.upload_media(media=photo)
  twitter.update_status(status='', media_ids=[response['media_id']])

class ReplyToTweet(TwythonStreamer):
  def __init__(self, *args, **kwargs):
    self.jobs_queue = kwargs["jobs_queue"]
    kwargs.pop('jobs_queue')
    TwythonStreamer.__init__(self, *args, **kwargs)

  def on_success(self, data):
    stdout("Received a tweet")

    tweet = data
    is_retweet = tweet.get('retweeted_status') != None
    from_self = tweet.get('user',{}).get('id_str','') == account_user_id

    if not is_retweet and not from_self:
      image_url = first_media_url(tweet)
      if image_url:
        stdout("Grabbing image from URL: %s" % image_url)
        resp = requests.get(image_url)
        if resp.status_code == 200:
          out_file = tempfile.NamedTemporaryFile(delete=False)
          out_file.write(resp.content)
          out_file.close()
          self.jobs_queue.put(out_file.name)
          stdout("Queued job for URL: %s" % image_url)
        else:
          stdout("Couldn't get media, status code was %d." % resp.status_code)
      else:
        stdout("No media found in tweet.")
    else:
      stdout("Tweet was a retweet or from this account.")

    return True

  def on_timeout(self, status):
    stdout("Something timed out with status %s" % status)
    return True

  def on_error(self, status):
    stdout("A streaming error occurred!")
    return True

def worker(jobs):
  outfile_index = 0
  configs = []
  for product in itertools.product(nlist, alist, mlist, replist):
    configs.append(product)

  while True:
    stdout("Worker is waiting for a job...")
    job = jobs.get()
    stdout("Got a job, starting...")
    config = configs[random.randrange(len(configs))]

    outfile_name = "output-%d.jpg" % outfile_index
    outfile_index += 1

    primitive(job, outfile_name, *config)
    stdout("Job is done!")

    upload_photo(outfile_name)
    os.remove(job)
    os.remove(outfile_name)
    stdout("Finished job and posted image.")

if __name__ == '__main__':
  stdout("Starting work")
  jobs = Queue()

  nlist = [50, 100, 150]
  alist = [0]
  mlist = [1, 5, 8]
  replist = [0, 20]
  nworkers = 1

  for i in xrange(nworkers):
    t = threading.Thread(target=worker, args=(jobs,))
    t.setDaemon(True)
    t.start()

  streamListener = ReplyToTweet(consumer_key, consumer_secret, access_token, access_token_secret, jobs_queue=jobs)
  streamListener.user()
  stdout("Streaming twitter data!")
