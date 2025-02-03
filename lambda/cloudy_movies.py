import requests, os, boto3, json, awsgi
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
MOVIE_INFO = 'https://www.themoviedb.org/movie/'
PROXY_ADDRESS = '172.31.35.24:4999'



app = Flask(__name__)
session = boto3.Session() # Uses profile defined in ~/.aws/credentials for AWS user
s3 = session.resource(service_name='s3')
bucket = s3.Bucket('cloudy-movies')



client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db['movies']



def check_if_stored(query):
    query_words = query.split()
    results = []
    for word in query_words:
        find = { '$or': [
            {'name': {'$regex': f'.*{word}.*', '$options': 'i'}},
            {'overview': {'$regex': f'.*{word}.*','$options': 'i'}}]}
        count = collection.count_documents(find)
        if count < 1: # Check if we got no stored data about query
            movies_data = query_tmdb(word)
            store_items(movies_data['results'])
        if len(word) > 2 and count < 10: # Check if it is more complex query and got low results count
            movies_data = query_tmdb(word)
            store_items(movies_data['results'])

        stored_movies = collection.find(find).sort({ 'vote_avg': -1 }).to_list()
        results += stored_movies

    results = json.dumps(results, default=str) # necessary for flask
    return results

def store_image(image_path):
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
            print('\tNo backdrop image, skipping...')
            continue
        search_result = collection.find({'movie_id': movie['id'] }).to_list()
        if search_result:
            print('\t[store_items]Found the movie in db, skipping...')
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
        collection.insert_one(document)
        print('\tStoring imgae in s3')
        store_image(image_path)
        results.append(document)
    return results

def query_tmdb(query):
    response = requests.get(f'http://{PROXY_ADDRESS}/proxy?url={API_URL}{SEARCH_ENDPOINT}{query}', headers={'Authorization': f'Bearer {ACCESS_TOKEN}'})
    print('\tRecieved data and storing in db')
    return response.json()

@app.route('/')
def search_title():
    # collection.drop()

    if request.query_string:
        query = request.args['query']
        stored_data = check_if_stored(query)
        if stored_data:
            print('\tReturnig data from DB')
            return stored_data, 200
        print('\tNothing found in DB trying TMDB API')

        movies_metadata = query_tmdb(query)
        results = store_items(movies_metadata['results'])

        return results, 200

    return 'Got no query string', 200

if __name__ == '__main__':      ### Use for local developent
    app.run(host='0.0.0.0', port=5003, debug=True)

# def lambda_handler(event, context):       ### Use with AWS lambda
#     return awsgi.response(app, event, context)

