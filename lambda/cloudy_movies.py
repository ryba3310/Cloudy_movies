import requests, os, boto3, json, awsgi
from flask import Flask, request
from pymongo import MongoClient
from PIL import Image
from io import BytesIO
from bson import json_util


MONGO_URI = os.environ['MONGO_URI']
DATABASE_NAME = os.environ['DATABASE_NAME']
ACCESS_TOKEN = os.environ['TMDB_TOKEN']
PROXY_ADDRESS = os.environ['PROXY_ADDRESS']
API_URL = 'https://api.themoviedb.org'
IMAGE_URL = 'https://image.tmdb.org/t/p/original'
SEARCH_ENDPOINT = '/3/search/movie?query='
MOVIE_ENDPOINT = '/3/movie/'
MOVIE_INFO = 'https://www.themoviedb.org/movie/'
MAX_RES_RESULTS = 5


app = Flask(__name__)
session = boto3.Session() # Uses profile defined in ~/.aws/credentials for AWS user or other environment variables, more in doc
s3 = session.resource(service_name='s3')
bucket = s3.Bucket('cloudy-movies')


client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db['movies']


def check_if_stored(query_words):
    """Returns list of stored movies data or False"""
    results = []
    count = 0
    for word in query_words:
        print(f'\t[check_if_stored] Checking db for word: {word}')
        find = { '$or': [
            {'name': {'$regex': f'.*{word}.*', '$options': 'i'}},
            {'overview': {'$regex': f'.*{word}.*','$options': 'i'}}]}
        count += collection.count_documents(find)
        print(f'\t[check_if_stored] Found {count} movies in db')

#################FIX and SPLIT#################
        if count < 1: # Check if we got no stored data about query
            return False
        if len(query_words) > 3 and count < 5: # Check if it is more complex query and got low results count
            MAX_RES_RESULTS = 15
            return False
        stored_movies = collection.find(find).sort({ 'vote_avg': -1 }).to_list()
        results += stored_movies

    results = json.dumps(results, default=str) # necessary to convert BSON doc into string recognized as JSON
    return results


def get_movies(query_words):
    """Return list of movies dictionaries"""
    stored_movies = check_if_stored(query_words)
    results = []
    if stored_movies:
        print('\t[get_movies]Returnig data from DB')
        return stored_movies
    # If not stored get data from TMDB
    print('\t[get_movies]Nothing found in DB trying TMDB API')
    for word in query_words:
        results += store_items(query_tmdb(word))

        print('\t[get_movies]Adding results')

    print('\t[get_movies]Returning results')
    print(results)
    return results


def store_image(image_path):
    """Store images in S3 bucket using ByteStram instead of file on disk"""
    obj = bucket.Object('movies' + image_path)
    upload_file_stream = BytesIO()
    print('\tPulling image')
    image = Image.open(requests.get(f'http://{PROXY_ADDRESS}/proxy_img?url={IMAGE_URL}{image_path}', stream=True).raw)
    image_format = image.format # format: JPG, PNG, etc.
    image.save(upload_file_stream, image_format)
    upload_file_stream.seek(0) # move to beginning of file
    print('\tConverted image to bytes, format: ' + image_format)
    obj.upload_fileobj(upload_file_stream, ExtraArgs={'ACL':'public-read'})
    print('\tStored backrop image in s3.')


def store_items(movies_metadata):
    results = []
    for movie in movies_metadata:
        image_path = movie['backdrop_path']
        if not image_path:
            print('\t[store_items]No backdrop image, skipping...')
            continue
        print('\t[store_items]Inserting data')
        movie_id = movie['id']
        movie_url_name = movie['original_title'].replace(' ', '-')
        document = {'movie_id': movie['id'],
                    'name': movie['original_title'],
                    'overview': movie['overview'],
                    'img_path': movie['backdrop_path'],
                    'tmdb_page': f'{MOVIE_INFO}{movie_id}-{movie_url_name}',
                    'vote_avg': str(movie['vote_average'])}
        search_result = collection.find({'movie_id': movie['id'] }).to_list()
        if search_result:
            print('\t[store_items]Found the movie in db, skipping...')
            results.append(document)
            continue
        results.append(document)
        print('\t[store_items]Inserting document into db...')
        collection.insert_one(document)
        store_image(image_path)
        document.pop('_id', None)
    return results


def query_tmdb(query):
    """Query TMDB though proxy container to bypass spawning NAT gateway in VPC"""
    print(f'Sending requests to TMDB with query: {query}')
    response = requests.get(f'http://{PROXY_ADDRESS}/proxy?url={API_URL}{SEARCH_ENDPOINT}{query}', headers={'Authorization': f'Bearer {ACCESS_TOKEN}'})
    print('\t[query_task]Recieved data and proceeding to store in db')
    response_json = response.json()['results']
    if len(response_json) > MAX_RES_RESULTS:
        return response_json[:MAX_RES_RESULTS]
    return response_json

@app.route('/')
def search_title():
    collection.drop()

    if request.query_string:
        query = request.args['query']
        stored_data = get_movies(query.split())
        return stored_data, 200

    return 'Got no query string', 200

if __name__ == '__main__':      ### Use for local developent
    app.run(host='0.0.0.0', port=5003, debug=True)

# def lambda_handler(event, context):       ### Use with AWS lambda
#     return awsgi.response(app, event, context)

