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
    print(event)

    pathParameters = event['pathParameters']
    print(pathParameters)
    if "userID" in pathParameters.keys():
        user = pathParameters['userID']
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('storyboard_users')
        response = table.get_item(
            Key={
                'user': user
            }
        )
        likes = response['Item']['likes']
        table = dynamodb.Table('storyboard_story')
        response = table.scan()
        items = response['Items']
        results = list()
        for item in items:
            if item['title'] in likes:
                results.append(item)
        print(results)
        return {
            'statusCode': 200,
            'headers': {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "*", "Access-Control-Allow-Headers": "*"},
            'body': dumps({"files": results})
        }
    else:
        genre = pathParameters['genre']
        print(genre)
        if genre == "all":
            dynamodb = session.resource('dynamodb', region_name='us-east-1')
            table = dynamodb.Table('storyboard_story')
            response = table.scan()
            print(response)
            results = response['Items']
            print(results)
        else:

            REGION = 'us-east-1'
            # add host here
            HOST = "search-storyboard-dm3yy2qp5minjs66mqlsvptyqa.us-east-1.es.amazonaws.com"
            INDEX = "storyboard"  # add index
            client = OpenSearch(hosts=[{
                'host': HOST,
                'port': 443
            }],
                http_auth=get_awsauth(REGION, 'es'),
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection)

            hitresults = set()
            # for k in keys:
            q = {'size': 100, 'query': {'multi_match': {'query': genre}}}
            res = client.search(index=INDEX, body=q)
            hits = res['hits']['hits']
            for hit in hits:
                hitresults.add(hit['_source']['objectKey'].replace("_", " "))

            print(hitresults)
            dynamodb = session.resource('dynamodb', region_name='us-east-1')
            table = dynamodb.Table('storyboard_story')
            response = table.scan()
            items = response['Items']
            results = list()
            for item in items:
                if item['title'] in hitresults:
                    results.append(item)

        return {
            'statusCode': 200,
            'headers': {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "*", "Access-Control-Allow-Headers": "*"},
            'body': dumps({"files": results})
        }
