import os
import boto3
import openai
import requests
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import json




def lambda_handler(event, context):
    event_data = json.loads(event['body'])
    print(event_data)
    # user = event_data['user']
    prompt = event_data['prompt']

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        temperature=0.3,
        max_tokens=150,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )

    output = response['choices'][0]['text']
    print(output)

    return {
        'statusCode': 200,
        'headers': {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "*", "Access-Control-Allow-Headers": "*"},
        'body': json.dumps({"outline": output})
    }
