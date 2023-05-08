import json
import boto3
import matplotlib.pyplot as plt
from collections import defaultdict
import matplotlib.gridspec as gridspec
import os
# from wordcloud import WordCloud, STOPWORDS
import subprocess
import sys
import shutil
import pip
import importlib

# subprocess.call('pip install https://github.com/sulunemre/word_cloud/releases/download/2/wordcloud-0.post1+gd8241b5-pp39-pypy39_pp73-manylinux_2_17_x86_64.manylinux2014_x86_64.whl --target=./'.split(),
#                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
# sys.path.insert(1, 'tmp')
def install_and_import(package):
    pip.main(['install', package,'-t','tmp' ])



install_and_import('wordcloud')
os.chdir(path="tmp")
shutil.make_archive("wordpkg", 'zip', "./")

s3 = boto3.client('s3')
s3.upload_file('wordpkg.zip', 'storyboard-story-balti', 'wordpkg.zip')
# s3.download_file('storyboard-story-balti', 'wordpkg.zip', '/tmp/wordpkg.zip')
# print(wordcloud.__version__)
# print("Imported all libraries")

# Create 2x2 sub plots
gs = gridspec.GridSpec(2, 2)
fig = plt.figure()


session = boto3.Session()


def lambda_handler(event, context):
    pathParameters = event['pathParameters']
    print(pathParameters)
    user = pathParameters['userID']

    s3 = session.client('s3')

    dynamodb = session.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('storyboard_users')
    response = table.get_item(
        Key={
            'user': user
        }
    )
    item = response['Item']
    # print(item)
    buys = item['buys']
    likes = item['likes']
    written = item['story']

    genres = defaultdict(int)
    expense = 0
    word_ct = 0
    text = ""
    table = dynamodb.Table('storyboard_story')
    for buy in buys:
        if buy!="":
            try:
                response = table.get_item(
                    Key={
                        'title': buy
                    }
                )
                item = response['Item']
                genres[item['genre']] += 1
                word_ct += float(item['word_ct'])
                expense += float(item['price'])
                obj = s3.get_object(Bucket='storyboard-story-balti',
                                    Key=item['title']+"_en.txt")
                text += obj['Body'].read().decode('utf-8')
            except:
                continue

    # plt.pie(genres.values(), labels=genres.keys(), autopct='%1.1f%%')
    # plt.show()
    ax1 = fig.add_subplot(gs[0, 1])  # row 0, col 0
    ax1.pie(genres.values(), labels=genres.keys(), autopct='%1.1f%%')
    ax1.set_title("Genre breakdown", fontsize=12)

    sales = 0

    for story in written:
        if story!="":
            response = table.get_item(
                Key={
                    'title': story
                }
            )
            try:
                item = response['Item']
                sales += item['price']*item['sales']
            except:
                continue

    likecount = defaultdict(int)
    for like in likes:
        if like!="":
            response = table.get_item(
                Key={
                    'title': like
                }
            )
            try:
                item = response['Item']
                likecount[item['genre']] += 1
            except:
                continue
    wordcloud = WordCloud(stopwords=STOPWORDS,
                          background_color="white").generate(text)

    # plt.imshow(wordcloud, interpolation='bilinear')
    ax3 = fig.add_subplot(gs[1, :])  # row 1, span all columns
    ax3.imshow(wordcloud, interpolation='bilinear')
    ax3.set_title("Your wordcloud", fontsize=12)
    # ax3.autoscale(enable=True, axis='both', tight=True)
    plt.axis("off")
    colors = [['palegreen'], ['coral'], ['lightskyblue'], ['pink']]
    rowcolors = ['palegreen', 'coral', 'lightskyblue', 'pink']
    # print("Total sales:", sales)
    # print("Total expense: ", expense)
    # print("Total words: ", word_ct)
    # print("Total likes: ", sum(likecount.values()))
    ax2 = fig.add_subplot(gs[0, 0])  # row 0, col 1
    tabdata = [[str(sales)+" $"], [str(expense)+" $"],
               [word_ct], [sum(likecount.values())]]
    tab = ax2.table(cellText=tabdata, rowLabels=[
                    "Total sales", "Total expense", "Total words", "Total likes"], loc='center right', colWidths=[0.5, 0.5], edges='closed')
    for c in tab.properties()['celld'].values():
        c.set(linewidth=0)
    ax2.set_title("Your stats", fontsize=12)
    tab[(0, 0)].set_facecolor('palegreen')
    tab[(1, 0)].set_facecolor('coral')
    tab[(2, 0)].set_facecolor('lightskyblue')
    tab[(3, 0)].set_facecolor('pink')

    # ax2.axis([0, 10, 0, 10])
    # ax2.text(3, 7, "Total sales: "+str(sales),ha='left', va='center',wrap=True,fontsize=12)
    # ax2.text(3, 6, "Total expense: "+str(expense),ha='left', va='center',wrap=True,fontsize=12)
    # ax2.text(3, 5, "Total words: "+str(word_ct),ha='left', va='center',wrap=True,fontsize=12)
    # ax2.text(3, 4, "Total likes: "+str(sum(likecount.values())),ha='left', va='center',wrap=True,fontsize=12)
    plt.axis("off")
    plt.tight_layout()
    # plt.show()
    lambda_path = "/tmp/"+user+"_wrapped.png"
    plt.savefig(lambda_path)
    file_name = user+"_wrapped.png"
    # file_name = title+'.png'
    # lambda_path = "/tmp/" + file_name
    # img_data = b64decode(response["data"][0]["b64_json"])
    # with open(lambda_path, 'wb') as handler:
    #     handler.write(img_data)

    s3path = 'images/'+file_name
    BUCKET_NAME = "storyboard-media-balti"
    s3 = session.resource("s3")
    resp = s3.Bucket(BUCKET_NAME).upload_file(lambda_path, s3path)
    s3url = s3.meta.client.generate_presigned_url('get_object', Params={
                                                  'Bucket': BUCKET_NAME, 'Key': s3path}, ExpiresIn=3600).split("?")[0]
    # print(resp)
    os.remove("/tmp/"+file_name)
    results = {'s3url':s3url}
    return {
        'statusCode': 200,
        'headers': {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "*", "Access-Control-Allow-Headers": "*"},
        'body': json.dumps(results)
    }
