# -*- coding: utf-8 -*-
"""
Created on Sat May 16 01:28:05 2020

@author: jeevan
"""

import boto3
import pymysql
import os
import json
import re

#s3 client
client = boto3.client('s3', region_name='us-east-1')

#translate client
translate = boto3.client(service_name='translate', region_name='us-east-1')

#comprehend client
comprehend = boto3.client(service_name='comprehend', region_name='us-east-1')

#database connection
cnx = pymysql.connect(host='jeevan.ckiej05nbavj.us-east-1.rds.amazonaws.com', 
                      user='jeevan', 
                      password='jeevan2020',
                      db='twitterdata')

cursor = cnx.cursor()
insCursor = cnx.cursor()

def send_data(input_path):
    file = open(input_path, 'r', encoding = 'utf-8')
    df = file.readlines()
    for item in df:
        temp = item.split(';')
        if(len(temp)==13):
            data = {'id':temp[0], 
                  'created_at':temp[1], 
                  'source':temp[2], 
                  'text':temp[3],
                  'lang':temp[4],
                  'favorite_count':temp[5], 
                  'retweet_count':temp[6], 
                  'original_author':temp[7], 
                  'possibly_sensitive':temp[8], 
                  'hashtags':temp[9],
                  'user_mentions':temp[10], 
                  'place':temp[11], 
                  'place_coord_boundaries':temp[12]
                  }
            #prepare the query to insert the data 
            insertQuery = ("INSERT INTO tweets(id ,created_at ,source , text ,lang ,favorite_count , retweet_count , original_author , possibly_sensitive , hashtags , user_mentions , place , place_coord_boundaries ) "
                    "VALUES(%(id)s, %(created_at)s, %(source)s, %(text)s, %(lang)s, %(favorite_count)s, %(retweet_count)s, %(original_author)s, %(possibly_sensitive)s, %(hashtags)s, %(user_mentions)s, %(place)s, %(place_coord_boundaries)s )")
            
            #inserting data to the database
            cursor.execute(insertQuery,data)
            print("query done \n")
            
            
            
            # here is the main part - comprehend.detect_sentiment is called
            sentimentData = comprehend.detect_sentiment(Text=temp[3], LanguageCode='en')
            
            
            
            # preparation of the data for the insert query
            
            qdata = {
                'id': temp[0],
                'created_at':temp[1],
                'text': temp[3],
                'Sentiment': "ERROR",
                'MixedScore': 0,
                'NegativeScore': 0,
                'NeutralScore': 0,
                'PositiveScore': 0,
              }
              
            if 'Sentiment' in sentimentData:
                qdata['Sentiment'] = sentimentData['Sentiment']
            if 'SentimentScore' in sentimentData:
                if 'Mixed' in sentimentData['SentimentScore']:
                  qdata['MixedScore'] = sentimentData['SentimentScore']['Mixed']
                if 'Negative' in sentimentData['SentimentScore']:
                  qdata['NegativeScore'] = sentimentData['SentimentScore']['Negative']
                if 'Neutral' in sentimentData['SentimentScore']:
                  qdata['NeutralScore'] = sentimentData['SentimentScore']['Neutral']
                if 'Positive' in sentimentData['SentimentScore']:
                  qdata['PositiveScore'] = sentimentData['SentimentScore']['Positive']
            
                query = ("INSERT INTO sentiments(id,created_at,text, sentiment, mixedScore, negativeScore, neutralScore, positiveScore) "
                           "VALUES(%(id)s,%(created_at)s,%(text)s, %(Sentiment)s, %(MixedScore)s, %(NegativeScore)s, %(NeutralScore)s, %(PositiveScore)s )")
            
            #inserting data to the database
            insCursor.execute(query,qdata)
            
            cnx.commit()
         
    file.close()       
    insCursor.close()
    cnx.close()
    

def transform_json(input_path, output_path,output):
    # Open the input file and load as json
    data_json = open(input_path, 'r').read()
    #Emoji patterns
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               "]+", flags=re.UNICODE)

    for json_object in data_json.split('\n')[:-1]:
        status = json.loads(json_object)
        new_entry=[]
        if hasattr(status,"extended_tweet"):
            temp_text = status.extended_tweet["full_text"]
        else:
            temp_text = status['text']
        temp_text = str.replace(temp_text,"…"," ")
        temp_text = str.replace(temp_text,"\n"," ")
        temp_text = str.replace(temp_text,"\\"," ")
        temp_text = re.sub(r':', '', temp_text)
        temp_text = re.sub(r'‚Ä¶', '', temp_text)
        #replace consecutive non-ASCII characters with a space
        temp_text = re.sub(r'[^\x00-\x7F]+',' ', temp_text)
        
        ## Translate Tweets text using AMAZON TRANSLATE
        
        if (status['lang'] == 'it'):
            # here is the main part - comprehend.detect_sentiment is called
            translateData = translate.translate_text(Text=temp_text,
                                                     SourceLanguageCode = "it",
                                                     TargetLanguageCode = "en")
            temp_text = translateData['TranslatedText']
        
        
        
            
        #remove emojis from tweet
        temp_text = emoji_pattern.sub(r'', temp_text)
        new_entry+= [status['id'], 
                     status['created_at'], 
                     status['source'],
                     temp_text,
                     status['lang'],
                     status['favorite_count'], 
                     status['retweet_count'],
                     status['user']['screen_name']]
        try:
            is_sensitive = status['possibly_sensitive']
        except KeyError:
            is_sensitive = None
        new_entry.append(is_sensitive)
        
        # hashtagas and mentiones are saved using comma separted
        hashtags = ", ".join([hashtag_item['text'] for hashtag_item in status['entities']['hashtags']])
        new_entry.append(hashtags)
        mentions = ", ".join([mention['screen_name'] for mention in status['entities']['user_mentions']])
        new_entry.append(mentions)
    
        #get location of the tweet if possible
        try:
            location = status['user']['location']
        except TypeError:
            location = None
        new_entry.append(location)
        
        try:
            coordinates = [coord for loc in status['place']['bounding_box']['coordinates'] for coord in loc]
        except TypeError:
            coordinates = None
        new_entry.append(coordinates)
        values = ';'.join(str(value) for value in new_entry)
        output.write(str(values + '\n').encode('utf-8'))
    
    print('Transformed {} to {}'.format(input_path, output_path))
    
    
def lambda_handler(event, context):
    # Get the info from the S3 Put event
    for record in event['Records']:
        bucket_name = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        local_path = '/tmp/' + key.split('/')[-1]
        # Download file from S3
        client.download_file(bucket_name, key, local_path)
        print("Downloaded s3 file, {}, to {}".format(key, local_path))
        # Transform the file
        output_path = '/tmp/output.txt'
        output = open(output_path, 'wb+')
        transform_json(local_path, output_path,output)
        output.close()
        
        send_data(output_path)
        object_name = str(record['eventTime'] + '_output.txt')
        with open(output_path, 'rb') as f:
            client.upload_fileobj(f, 'twitterdatadb', object_name)
        f.close()
        os.remove(local_path)
        os.remove(output_path)
