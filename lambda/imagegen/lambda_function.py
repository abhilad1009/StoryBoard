import os
import boto3
import openai
import requests
from base64 import b64decode
import json


# PROMPT = "A bustling New York street"

session = boto3.Session()


def lambda_handler(event, context):
    data = json.loads(event['body'])
    print(data)
    title = data['title']
    prompt = data['prompt']

    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="256x256",
        response_format="b64_json",
    )
    print(response["data"][0]["b64_json"])
    try:
        os.mkdir(path="/tmp")
    except:
        pass
    file_name = title+'.png'
    lambda_path = "/tmp/" + file_name
    img_data = b64decode(response["data"][0]["b64_json"])
    with open(lambda_path, 'wb') as handler:
        handler.write(img_data)


    s3_path = "images/"+file_name
    BUCKET_NAME = "storyboard-media-balti"
    s3 = session.resource("s3")
    resp = s3.Bucket(BUCKET_NAME).upload_file(lambda_path, s3_path)
    s3url = s3.meta.client.generate_presigned_url(
        'get_object', Params={'Bucket': BUCKET_NAME, 'Key': s3_path}, ExpiresIn=3600).split("?")[0]
    print(resp)
    os.remove("/tmp/"+file_name)
    # print(img_data)
    ans = {"imgurl": s3url}

    return {
        'statusCode': 200,
        'headers': {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "*", "Access-Control-Allow-Headers": "*"},
        'body': json.dumps(ans)
    }
