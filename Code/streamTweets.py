# -*- coding: utf-8 -*-
"""
Created on Mon May 11 15:17:46 2020

@author: avlok-pc
"""

import tweepy
import sys
import boto3
import jsonpickle
import json

    
# authorization tokens
consumer_key = "oZRn3u3RCyfHJvhDL4uKWqkhV"
consumer_secret = "mHCjVDYzmmwMnneTmD4mksWyrcBqXYrxTHCcgw8bqcDtwdt7Hj"
access_key= "1257888661871321088-IaxCzs75p1mF8egGdy8vp1jmSDgfsN"
access_secret = "zSahqTChqE7TUfPlXq8zW9egnFXz1FURCbG7wmwhJYQa2"

stream_name = "twitterstream"
shardCount = 1

kinesis = boto3.client('kinesis', region_name='us-east-1')

kinesisRecords = []
sendKinesis = False
count = 0

# StreamListener class inherits from tweepy.StreamListener and overrides on_status/on_error methods.
class StreamListener(tweepy.StreamListener):
   
    
    def on_status(self, status):
        #print(json.dumps(status._json))
        global kinesisRecords
        global sendKinesis 
        global count
        
        encodedValues = bytes(str(json.dumps(status._json) + '\n').encode('utf-8'))
        
        #print(encodedValues)
        
        # create a dict object of the row
        kinesisRecord = {
            "Data": encodedValues, # data byte-encoded
            "PartitionKey": str(shardCount) # some key used to tell Kinesis which shard to use
        }


        kinesisRecords.append(kinesisRecord) # add the object to the list
        
        # check conditional whether ready to send
        if len(kinesisRecords) == 100: # if we have 500 records packed up, then proceed
            sendKinesis = True # set the flag

        
        if sendKinesis == True:
            print (len(kinesisRecords))
            # put the records to kinesis
            response = kinesis.put_records(Records= kinesisRecords,
                                           StreamName = stream_name
                                           )
            count = count + 1
            print("Kinesis streamed for " + str(count))
            #print (kinesisRecords)
            #sys.exit()
            # resetting values ready for next loop
            kinesisRecords = [] # empty array
            sendKinesis = False # reset flag
        
        if(count == 10):
            sys.exit()
    
    def on_error(self, status_code):
        print("Encountered streaming error (", status_code, ")")
        sys.exit()
    
    
if __name__ == "__main__":
    
    
    # complete authorization and initialize API endpoint
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    api = tweepy.API(auth)

    # initialize stream
    streamListener = StreamListener()
    stream = tweepy.Stream(auth=api.auth, listener=streamListener,tweet_mode='extended')
    tags = ["covid"]
    stream.filter(track=tags, languages = ['it', 'en'])
    