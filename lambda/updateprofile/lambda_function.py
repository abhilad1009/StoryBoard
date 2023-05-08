import os
import boto3
import json
session = boto3.Session()


def lambda_handler(event, context):
    event_data = json.loads(event['body'])
    user = event_data['user']
    title = event_data['title']
    action = event_data['action']

    if action == "LIKE":
        dynamodb = session.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('storyboard_users')
        response = table.get_item(
            Key={
                'user': user
            }
        )
        item = response['Item']
        print(item)
        likes = item['likes']
        likes.append(title)
        table.update_item(
            Key={
                'user': user
            },
            UpdateExpression="set likes = :l",
            ExpressionAttributeValues={
                ':l': likes
            },
            ReturnValues="UPDATED_NEW"
        )
    elif action == "BUY":
        dynamodb = session.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('storyboard_users')
        response = table.get_item(
            Key={
                'user': user
            }
        )
        item = response['Item']
        print(item)
        buys = item['buys']
        buys.append(title)
        table.update_item(
            Key={
                'user': user
            },
            UpdateExpression="set buys = :b",
            ExpressionAttributeValues={
                ':b': buys
            },
            ReturnValues="UPDATED_NEW"
        )

        table = dynamodb.Table('storyboard_story')
        response = table.get_item(
            Key={
                'title': title
            }
        )
        item = response['Item']
        sales = item['sales']
        sales += 1
        table.update_item(
            Key={
                'title': title
            },
            UpdateExpression="set sales = :s",
            ExpressionAttributeValues={
                ':s': sales
            },
            ReturnValues="UPDATED_NEW"
        )

    return {
        'statusCode': 200,
        'headers': {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "*", "Access-Control-Allow-Headers": "*"},
    }
