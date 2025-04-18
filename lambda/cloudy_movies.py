import requests, os, boto3, json, awsgi, sys
from flask import Flask, request
from pymongo import MongoClient, UpdateOne
from concurrent.futures import ThreadPoolExecutor
from tenacity import retry, stop_after_attempt, wait_exponential
import logging


MONGO_URI = os.environ['MONGO_URI']
DATABASE_NAME = os.environ['DATABASE_NAME']
ACCESS_TOKEN = os.environ['TMDB_TOKEN']
PROXY_ADDRESS = os.environ['PROXY_ADDRESS']
API_URL = 'https://api.themoviedb.org'
IMAGE_URL = 'https://image.tmdb.org/t/p/original'
SEARCH_ENDPOINT = '/3/search/movie?query='
MOVIE_ENDPOINT = '/3/movie/'
MOVIE_INFO = 'https://www.themoviedb.org/movie/'


logger = logging.getLogger()
logger.setLevel(logging.INFO)
sh = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s [%(filename)s.%(funcName)s:%(lineno)d] %(message)s', datefmt='%a, %d %b %Y %H:%M:%S')
sh.setFormatter(formatter)
logger.addHandler(sh)


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
    regex_conditions = []
    count = 0

    # Build a single query with all words
    for word in query_words:
        regex_conditions.append({'name': {'$regex': f'.*{word}.*', '$options': 'i'}})
        regex_conditions.append({'overview': {'$regex': f'.*{word}.*', '$options': 'i'}})

    find_query = {'$or': regex_conditions}
    logger.info(f'\t Checking db for word: {word}')
    count = collection.count_documents(find_query)
    logger.info(f'\t Found {count} movies in db')

    if count < 1: # Check if we got no stored data about query
        return False

    if len(query_words) > 2 and count < 10:
        return False

    stored_movies = collection.find(find_query).sort({ 'vote_avg': -1 }).to_list()
    results += stored_movies

    results = json.dumps(results, default=str) # necessary to convert BSON doc into string recognized as JSON
    return results


def get_movies(query_words):
    """Return list of movies dictionaries"""
    stored_movies = check_if_stored(query_words)
    if stored_movies:
        logger.info('\tReturnig data from DB')
        return stored_movies
    # If not stored get data from TMDB
    logger.info('\tNothing found in DB trying TMDB API')
    for word in query_words:
        store_items(query_tmdb(word))
        logger.info('\tStored results in DB')

    return check_if_stored(query_words)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def store_image(image_path):
    """Store images in S3 bucket using ByteStram instead of file on disk"""
    try:
        # Check if already exists
        obj = bucket.Object('movies' + image_path)
        try:
            obj.load()  # Check if exists
            logger.info(f'\tImage {image_path} exists, skipping')
            return
        except:
            pass  # Doesn't exist, proceed

        # Stream directly from source to S3
        with requests.get(
            f'http://{PROXY_ADDRESS}/proxy_img?url={IMAGE_URL}{image_path}',
            stream=True
        ) as r:
            r.raise_for_status()

            # Get content type from response or image
            content_type = r.headers.get('content-type', 'image/jpeg')

            # Upload directly from stream
            obj.upload_fileobj(
                r.raw,
                ExtraArgs={
                    'ACL': 'public-read',
                    'ContentType': content_type
                })

    except Exception as e:
        print(f'\tError storing image {image_path}: {str(e)}')
        raise


def store_items(movies_metadata):
    results = []
    operations = []
    image_paths = []

    for movie in movies_metadata:
        if not movie['backdrop_path']:
            logger.info('\tNo backdrop image, skipping...')
            continue

        image_paths.append(movie['backdrop_path'])
        movie_id = movie['id']
        movie_url_name = movie['original_title'].replace(' ', '-')
        document = {'movie_id': movie['id'],
                    'name': movie['original_title'],
                    'overview': movie['overview'],
                    'img_path': movie['backdrop_path'],
                    'tmdb_page': f'{MOVIE_INFO}{movie_id}-{movie_url_name}',
                    'vote_avg': str(movie['vote_average'])}

        # Check if the movie is already stored
        search_result = collection.find({'movie_id': movie['id'] }).to_list()
        if search_result:
            logger.info('\tFound the movie in db, skipping...')
            results.append(document)
            continue

        # Build results from parsed data and items inserted
        operations.append(UpdateOne(
                {'movie_id': movie_id},
                {'$setOnInsert': document},
                upsert=True
            )
        )

    logger.info('\tInserting document into db...')
    if operations:
        try:
            collection.bulk_write(operations, ordered=False)
        except BulkWriteError as bwe:
            logger.info(f"\tBulk write error: {bwe.details}")

    # Store images using parallel processing
    if image_paths:
        with ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(store_image, image_paths)


def query_tmdb(query):
    """Query TMDB though proxy container to bypass spawning NAT gateway in VPC"""
    logger.info(f'\tSending requests to TMDB with query: {query}')
    try:
        with requests.get(f'http://{PROXY_ADDRESS}/proxy?url={API_URL}{SEARCH_ENDPOINT}{query}', 
                          headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}) as res:
            res.raise_for_status()
            logger.info('\tRecieved data and proceeding to store in db')
            return res.json()['results']
    except requests.exceptions.RequestException as e:
        print(f"TMDB API request failed: {str(e)}")
        return []


@app.route('/')
def search_title():
    collection.drop()

    if request.query_string:
        query = request.args['query']
        stored_data = get_movies(query.split())
        return stored_data, 200

    return 'Got no query string', 200


#if __name__ == '__main__':      ### Use for local developent
#    app.run(host='0.0.0.0', port=5003, debug=True)


def lambda_handler(event, context):       ### Use with AWS lambda
    return awsgi.response(app, event, context)

