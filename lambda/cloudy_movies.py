import requests, os, boto3#, awsgi
from flask import Flask, request
from pymongo import MongoClient
from PIL import Image
from io import BytesIO



MONGO_URI = os.environ['MONGO_URI']
DATABASE_NAME = os.environ['DATABASE_NAME']
ACCESS_TOKEN = os.environ['TMDB_TOKEN']
API_URL = 'https://api.themoviedb.org'
IMAGE_URL = 'https://image.tmdb.org/t/p/original'
SEARCH_ENDPOINT = '/3/search/movie?query='
MOVIE_ENDPOINT = '/3/movie/'


app = Flask(__name__)
session = boto3.Session() # Uses profile defined in ~/.aws/credentials for AWS user
s3 = session.resource(service_name='s3')
bucket = s3.Bucket('cloudy-movies')


client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db['movies']



# def check_if_stored(title):
#     stored_titles = True # db.get()
#     return stored_titles or None


def store_image(image_path):
    image = Image.open(requests.get(f'{IMAGE_URL}{image_path}', stream=True).raw)
    bucket.upload_fileobj(image, image_path)

def store_items(movies_metadata):
    for movie in movies_metadata:
        if collection.find(({'movie_id': movie['id]']})):
            continue
        movie_data = requests.get(f'{API_URL}{MOVIE_ENDPOINT}{movie['id']}')
        collection.insert()
        store_image(movie_data['backdrop_path'])
    
@app.route('/')
def search_title():

    if request.query_string:
        query = request.args['query']
        # stored_data = check_if_stored(query)
        # if check_if_stored:
        #     return stored_data
        response = requests.get(f'http://172.31.35.24:4999/proxy?url={API_URL}{SEARCH_ENDPOINT}{query}', headers={'Authorization': f'Bearer {ACCESS_TOKEN}'})
        movie_metadata = response.json()
        store_items(movie_metadata['results'])
        # movie_metadata['img_s3_path'] = store_img(movie_metadata['belongs_to_collection']['backdrop_path'])
        # return movie_metadata

    return 'Got no query string', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)

# def lambda_handler(event, context):
#     return awsgi.response(app, event, context)