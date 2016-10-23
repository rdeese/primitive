from Queue import Queue
import os
import json
import requests
import tempfile
import itertools
import random
import threading
import subprocess
import sys

from twython import Twython
from twython import TwythonStreamer
# from tweepy.streaming import StreamListener
# from tweepy import OAuthHandler
# from tweepy import Stream
# from tweepy import API

consumer_key = 'qFPPU65i8vHEalWQDrmM61aOz' 
consumer_secret = 'GKExu6pRtGFL9EEWRibcAWNPwU4Ewhphzu53Co2H7zmKDSG5Am' 
access_token = '789981061186920448-34VL5BtNTf7vd1aBNBAfJ5gUSxRS3pV'
access_token_secret = 'HZ3alPBJUxfFAVFTYrw9r1DPuCBKfovwfQER5QrmSxWv2'
account_user_id = '789981061186920448'

twitter = Twython(consumer_key, consumer_secret, access_token, access_token_secret)

# auth = OAuthHandler(consumer_key, consumer_secret)
# auth.set_access_token(access_token, access_token_secret)
# twitterApi = API(auth)

def primitive(i, o, n, a, m, rep):
    args = (i, o, n, a, m, rep)
    cmd = 'primitive -r 256 -bg "#FFFFFF" -i %s -o %s -n %d -a %d -m %d -rep %d' % args
    sys.stdout.write("Starting primitive job...\n")
    sys.stdout.write("%s\n" % cmd)
    sys.stdout.flush()
    subprocess.call(cmd, shell=True)

def upload_photo(path):
  photo = open(path, 'rb')
  resp = twitter.upload_media(media=photo)
  twitter.update_status(status='', media_ids=[response['media_id']])

class ReplyToTweet(TwythonStreamer):
  def __init__(self, *args, **kwargs):
    self.jobs_queue = kwargs["jobs_queue"]
    kwargs.pop('jobs_queue')
    TwythonStreamer.__init__(self, *args, **kwargs)

  def image_url(self, tweet):
    entities = tweet.get("extended_entities")
    if entities:
      media = entities.get("media")
      if type(media) == list:
        media_entry = media[0]
        if media_entry.get("type") == "photo":
          return media_entry.get("media_url")
    return None

  def on_success(self, data):
    # tweet = json.loads(data.strip())
    tweet = data
    # # print json.dumps(tweet, sort_keys=True, indent=4, separators=(',', ': '))
    
    retweeted = tweet.get('retweeted')
    from_self = tweet.get('user',{}).get('id_str','') == account_user_id

    sys.stdout.write("Retweeted: "+str(retweeted)+"  from_self: "+str(from_self)+"\n")
    sys.stdout.flush()

    sys.stdout.write("Received a tweet\n")
    sys.stdout.flush()

    if retweeted is not None and not retweeted and not from_self:
      image_url = self.image_url(tweet)
      if image_url:
        sys.stdout.write("Grabbing image from URL: %s\n" % image_url)
        sys.stdout.flush()
        resp = requests.get(image_url)
        # print "Response status is", resp.status_code
        if resp.status_code == 200:
          out_file = tempfile.NamedTemporaryFile(delete=False)
          out_file.write(resp.content)
          out_file.close()
          self.jobs_queue.put(out_file.name)
          sys.stdout.write("Queued job for URL: %s\n" % image_url)
          sys.stdout.flush()
        else:
          sys.stdout.write("Couldn't get media, status code was %d.\n" % resp.status_code)
          sys.stdout.flush()
      else:
        sys.stdout.write("No media found in tweet.\n")
        sys.stdout.flush()
    else:
      sys.stdout.write("Tweet was a retweet or from this account.")
      sys.stdout.flush()

    return True

  def on_timeout(self, status):
    sys.stdout.write("Something timed out with status %s\n" % status)
    sys.stdout.flush()
    # print status
    return True

  def on_error(self, status):
    sys.stdout.write("A tweepy error occurred! :(\n")
    sys.stdout.flush()
    # print status
    return True

def worker(jobs):
  outfile_index = 0
  configs = []
  for product in itertools.product(nlist, alist, mlist, replist):
    configs.append(product)

  while True:
    sys.stdout.write("Worker is waiting for a job...\n")
    sys.stdout.flush()
    job = jobs.get()
    sys.stdout.write("Got a job, starting...\n")
    sys.stdout.flush()
    # print job
    config = configs[random.randrange(len(configs))]
    # print config
    outfile_name = "output-%d.jpg" % outfile_index
    outfile_index += 1
    primitive(job, outfile_name, *config)
    sys.stdout.write("Job is done!\n")
    sys.stdout.flush()
    upload_photo(outfile_name)
    os.remove(job)
    os.remove(outfile_name)
    sys.stdout.write("Finished job and posted image.\n")
    sys.stdout.flush()

if __name__ == '__main__':
  sys.stdout.write("Starting work\n")
  sys.stdout.flush()
  jobs = Queue()

  nlist = [400] # [50, 100, 150]
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
  sys.stdout.write("Streaming twitter data!\n")
  sys.stdout.flush()
