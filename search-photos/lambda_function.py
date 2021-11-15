import json
import boto3
import requests



host_address = 'https://search-photos-bpyag6mxbm4cvvdhp66wg4wdtm.us-west-2.es.amazonaws.com'
region = 'us-west-2' 


def get_url(index, cat, keyword):
	url = host_address + '/' + index + '/' + cat + '/_search?q=' + keyword.lower()
	return url
    
    
def lambda_handler(event, context):
	print(event)
	headers = { "Content-Type": "application/json" }
	lex = boto3.client('lex-runtime')
	query = event["queryStringParameters"]["q"]
	lex_response = lex.post_text(botName='photoalbums',botAlias='photoalbums',userId='firstuser',inputText=query)
	print(lex_response)
	slots = lex_response['slots']
	img_list = []
	for i, tag in slots.items():
		if tag:
			url = get_url('photos', 'Photo', tag)
			print("ES URL --- {}".format(url))
			es_response = requests.get(url, auth=("photoalbum", "Photo123!"), headers=headers)
			print(json.loads(es_response.text))
			es_src = json.loads(es_response.text)['hits']['hits']
			print(es_src)
			for photo in es_src:
				labels = [word.lower() for word in photo['_source']['labels']]
				if tag in labels:
					objectKey = photo['_source']['objectKey']
					img_url = 'https://6998-photo.s3.amazonaws.com/' + objectKey
					if img_url not in img_list:
						img_list.append(img_url)
	print(img_list)
	if img_list:
		return {
			'statusCode': 200,
			'headers': {
				"Access-Control-Allow-Origin": "*",
				'Content-Type': 'application/json'
			},
			'body': json.dumps(img_list)
		}
	else:
		return {
			'statusCode': 200,
			'headers': {
				"Access-Control-Allow-Headers": 'Content-Type',
				"Access-Control-Allow-Origin": "*",
				"Access-Control-Allow-Methods": 'OPTIONS, POST, GET, PUT',
				'Content-Type': 'application/json'
			},
			'body': json.dumps("No such photos.")
			
		}
	