import json
import urllib.parse
import boto3
from datetime import *
import requests
from requests_aws4auth import AWS4Auth


def detect_labels(photo, bucket):
    rek = boto3.client('rekognition')
    response = rek.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':photo}},
        MaxLabels=10)

    print('Detected labels for ' + photo) 
    print(response['Labels'])   

    return response['Labels']


def lambda_handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        size = record['s3']['object']['size']
    print('bucket=',bucket)
    print('key=',key)
    labels = detect_labels(key, bucket) #detect the labels
    print(labels)
    
    s3client = boto3.client('s3')
    s3_response = s3client.head_object(Bucket=bucket,Key=key)
    print('Metadata is ', s3_response['Metadata'])
    json_object = {}
    json_object['objectKey'] = key
    json_object['bucket'] = bucket
    json_object['createdTimestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    json_object['labels'] = []
    for label in labels:
        json_object['labels'].append(label['Name'])
    if 'customlabels' in s3_response['Metadata']:
        for cstlabels in s3_response['Metadata']['customlabels'].split(', '):
            json_object['labels'].append(cstlabels)
    
    print("JSON OBJECT --- {}".format(json_object)) #create the json object
    
    #put the object into search
    #host_address = 'https://vpc-photos-bpyag6mxbm4cvvdhp66wg4wdtm.us-west-2.es.amazonaws.com'
    host_address = 'https://search-photos-bpyag6mxbm4cvvdhp66wg4wdtm.us-west-2.es.amazonaws.com'
    index = 'photos'
    cat = 'Photo'
    headers = { "Content-Type": "application/json" }
    region = 'us-west-2' 
    service = 'es'
    url = host_address + '/' + index + '/' + cat
    print(url)
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    response = requests.post(url, auth=("photoalbum", "Photo123!"), json=json_object, headers=headers)
    print(response.text)
    return {
        'statusCode': 200,
        'headers': {
            "Access-Control-Allow-Origin": "*",
            'Content-Type': 'application/json'
        },
        'body': json.dumps("The image has been detected and uploaded!")
    }