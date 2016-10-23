from Queue import Queue
import os
import json
import requests
import tempfile
import itertools
import random
import threading
import subprocess

from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy import API

consumer_key = 'qFPPU65i8vHEalWQDrmM61aOz' 
consumer_secret = 'GKExu6pRtGFL9EEWRibcAWNPwU4Ewhphzu53Co2H7zmKDSG5Am' 
access_token = '789981061186920448-34VL5BtNTf7vd1aBNBAfJ5gUSxRS3pV'
access_token_secret = 'HZ3alPBJUxfFAVFTYrw9r1DPuCBKfovwfQER5QrmSxWv2'
account_user_id = '789981061186920448'

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
twitterApi = API(auth)

def primitive(i, o, n, a, m, rep):
    args = (i, o, n, a, m, rep)
    cmd = 'primitive -r 256 -bg "#FFFFFF" -i %s -o %s -n %d -a %d -m %d -rep %d' % args
    print "Starting primitive job..."
    print cmd
    subprocess.call(cmd, shell=True)

class ReplyToTweet(StreamListener):
  def __init__(self, api=None, jobs_queue=None):
    StreamListener.__init__(self, api=None)
    self.jobs_queue = jobs_queue

  def on_data(self, data):
    tweet = json.loads(data.strip())
    # # print json.dumps(tweet, sort_keys=True, indent=4, separators=(',', ': '))
    
    retweeted = tweet.get('retweeted')
    from_self = tweet.get('user',{}).get('id_str','') == account_user_id

    print "Received a tweet"

    if retweeted is not None and not retweeted and not from_self:
      if "extended_entities" in tweet and tweet["extended_entities"]["media"][0]["type"] == "photo":
        media_url = tweet["extended_entities"]["media"][0]["media_url"]
        print "Grabbing image from URL: ", media_url
        resp = requests.get(media_url)
        # print "Response status is", resp.status_code
        if resp.status_code == 200:
          out_file = tempfile.NamedTemporaryFile(delete=False)
          out_file.write(resp.content)
          out_file.close()
          self.jobs_queue.put(out_file.name)
      # else:
      #   print "no media"

    return True

  def on_error(self, status):
    print "A tweepy error occurred! :("
    # print status
    return True

def worker(jobs):
  outfile_index = 0
  configs = []
  for product in itertools.product(nlist, alist, mlist, replist):
    configs.append(product)

  while True:
    job = jobs.get()
    # print job
    config = configs[random.randrange(len(configs))]
    # print config
    outfile_name = "output-%d.jpg" % outfile_index
    outfile_index += 1
    primitive(job, outfile_name, *config)
    twitterApi.update_with_media(outfile_name)
    os.remove(job)
    os.remove(outfile_name)
    print "Finished job and posted image."

if __name__ == '__main__':
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

  streamListener = ReplyToTweet(jobs_queue = jobs)
  twitterStream = Stream(auth, streamListener)
  twitterStream.userstream(_with='user', async=True)
