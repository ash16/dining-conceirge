import json
import boto3

lec_client = boto3.client('lex-runtime')

def lambda_handler(event, context):
    userid = event['eventid']
    ip = event['key']
    
    response = lec_client.post_text(
        botAlias = 'Latest_DiningBot',
        botName = 'DiningBot',
        userId =  "123",
        inputText = userid
        )
        
    return response