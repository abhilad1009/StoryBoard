import os
import boto3
import requests
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import json
import decimal

session = boto3.Session()

def dumps(item: dict) -> str:
    return json.dumps(item, default=default_type_error_handler)


def default_type_error_handler(obj):
    if isinstance(obj, decimal.Decimal):
        return int(obj)
    raise TypeError

def get_awsauth(region, service):
    cred = session.get_credentials()
    return AWS4Auth(cred.access_key,
                    cred.secret_key,
                    region,
                    service,
                    session_token=cred.token)


def lambda_handler(event, context):

    pathParameters = event['pathParameters']
    print(pathParameters)
    storyid, lang, read = pathParameters['storyId'].split('_')
    print(storyid, lang, read)
    dynamodb = session.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('storyboard_story')
    response = table.get_item(
        Key={
            'title': storyid
        }
    )
    print(response)
    if(read!='read'):
        results = response['Item']
        return {
        'statusCode': 200,
        'headers': {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "*", "Access-Control-Allow-Headers": "*"},
        'body': dumps(results)
        }
    else:
        results = {'title':response['Item']['title'],"author":response['Item']['author'],'mood_color':response['Item']['mood_color']}
        s3 = session.client('s3')
        bucket = 'storyboard-story-balti'
        path = storyid+'_'+lang+'.txt'
        obj = s3.get_object(Bucket='storyboard-story-balti', Key=path)
        content = obj['Body'].read().decode('utf-8')
        results['story'] = content
        print(results)
        return {
            'statusCode': 200,
            'headers': {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "*", "Access-Control-Allow-Headers": "*"},
            'body': dumps({"files": results})
        }

