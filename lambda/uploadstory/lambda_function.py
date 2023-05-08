import os
import boto3
import openai
import requests
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import json


session = boto3.Session()


def get_awsauth(region, service):
    cred = session.get_credentials()
    return AWS4Auth(cred.access_key,
                    cred.secret_key,
                    region,
                    service,
                    session_token=cred.token)



defaultRegion = 'us-east-1'
defaultUrl = 'https://polly.us-east-1.amazonaws.com'


def connectToPolly(regionName=defaultRegion, endpointUrl=defaultUrl):
    return session.client('polly', region_name=regionName, endpoint_url=endpointUrl)


"""
Languege codes

English en 
French	fr
Hindi	hi
Japanese	ja

"""


def lambda_handler(event, context):
    event_data = json.loads(event['body'])

    print(event_data)

    user = event_data['author']
    title = event_data['title']
    story = event_data['content']
    genre = event_data['genre']
    price = event_data['price']
    imgsrc = event_data['imgsrc']

    # print(title, story, genre)

    polly = connectToPolly()

    file_name = title + ".mp3"
    resp = polly.synthesize_speech(
        OutputFormat='mp3', Text=story, VoiceId='Brian')
    soundfile = open('/tmp/'+file_name, 'wb')
    soundBytes = resp['AudioStream'].read()
    soundfile.write(soundBytes)
    soundfile.close()
    BUCKET_NAME = "storyboard-media-balti"

    lambda_path = "/tmp/" + file_name
    s3_path = file_name
    # os.system('echo testing... >'+lambda_path)
    s3 = session.resource("s3")
    s3.meta.client.upload_file(lambda_path, BUCKET_NAME, "audio/"+file_name)

    ########## French ###########
    BUCKET_NAME = "storyboard-story-balti"

    client = session.client('translate', region_name="us-east-1")
    response = client.translate_text(Text=story,
                                     SourceLanguageCode='en',
                                     TargetLanguageCode='fr')

    output = response['TranslatedText']
    file_name = title + "_fr.txt"
    s3_path = file_name
    lambda_path = "/tmp/" + file_name
    with open(lambda_path, 'w', encoding='utf8') as f:
        f.write(output)

    s3.meta.client.upload_file(lambda_path, BUCKET_NAME, file_name)

    ########## Hindi ###########
    response = client.translate_text(Text=story,
                                     SourceLanguageCode='en',
                                     TargetLanguageCode='hi')

    output = response['TranslatedText']
    file_name = title + "_hi.txt"
    s3_path = file_name
    lambda_path = "/tmp/" + file_name
    with open(lambda_path, 'w', encoding='utf8') as f:
        f.write(output)

    s3.meta.client.upload_file(lambda_path, BUCKET_NAME, file_name)

    ########## Japanese ###########
    response = client.translate_text(Text=story,
                                     SourceLanguageCode='en',
                                     TargetLanguageCode='ja')

    output = response['TranslatedText']
    file_name = title + "_ja.txt"
    s3_path = file_name
    lambda_path = "/tmp/" + file_name
    with open(lambda_path, 'w', encoding='utf8') as f:
        f.write(output)

    s3.meta.client.upload_file(lambda_path, BUCKET_NAME, file_name)

    ########## English ###########

    file_name = title + "_en.txt"
    s3_path = file_name
    lambda_path = "/tmp/" + file_name
    with open(lambda_path, 'w', encoding='utf8') as f:
        f.write(story)

    s3.meta.client.upload_file(lambda_path, BUCKET_NAME, file_name)

    os.remove("/tmp/"+title+".mp3")
    os.remove("/tmp/"+title+"_en.txt")
    os.remove("/tmp/"+title+"_fr.txt")
    os.remove("/tmp/"+title+"_hi.txt")
    os.remove("/tmp/"+title+"_ja.txt")

    ############ Summary ##############
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=story+"\n\ntl;dr:",
        temperature=0,
        max_tokens=64,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        stop=[";"]
    )

    summary = response['choices'][0]['text']
    print(summary)

    response = openai.Completion.create(
    model="text-davinci-003",
    prompt="Decide if the emotion of story is happy, sad, mystery, romantic, angry, fear or disgust.\n\nStory: "+ story+"\nEmotion:",
    temperature=0,
    max_tokens=60,
    top_p=1,
    frequency_penalty=0.5,
    presence_penalty=0
    )
    mood = response['choices'][0]['text']
    print(mood)

    ############ Mood color ##############
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt="The CSS code for "+mood+" mood is:\n\nbackground-color: #",
        temperature=0,
        max_tokens=64,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        stop=[";"]
    )

    mood_color = response['choices'][0]['text']
    print(mood_color)

    ############ Word count ##############
    word_ct = len(story.split())

    ############ DynamoDB ##############
    story_data = {"title": title, "author": user, "summary": summary, "word_ct": word_ct,
                  "genre": genre, "mood_color": mood_color, "sales": 0, "price": price, "imgsrc": imgsrc}

    dynamodb = session.resource('dynamodb', region_name='us-east-1')

    table = dynamodb.Table('storyboard_story')

    response = table.put_item(
        Item=story_data
    )

    table = dynamodb.Table('storyboard_users')
    response = table.get_item(
        Key={
            'user': user
        }
    )
    item = response['Item']
    # print(item)
    written = item['story']
    written.append(title)
    table.update_item(
        Key={
            'user': user
        },
        UpdateExpression="set story = :l",
        ExpressionAttributeValues={
            ':l': written
        },
        ReturnValues="UPDATED_NEW"
    )

    ############ ElasticSearch ##############
    elastic_data = {'objectKey': title.replace(" ", "_"),
                    'genre': genre}
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

    resp = client.index(index='storyboard', id=title.replace(
        " ", "_"), body=elastic_data)
    # print(resp)

    return {
        'statusCode': 200,
        'headers': {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "*", "Access-Control-Allow-Headers": "*"},
        'body': json.dumps('Upload successful!')
    }
