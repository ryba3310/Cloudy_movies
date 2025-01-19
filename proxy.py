from flask import Flask, request, Response
import requests



app = Flask(__name__)



@app.route('/proxy', methods=['GET'])
def proxy():
    if request.query_string:
        url = request.args.get('url')
        token = request.headers['Authorization']
        if url:
            print(f'Doing request to: {url}')
            response = requests.get(url, headers={'Authorization': f'{token}'})
            return Response(response.content)
        else:
            return "Invalid URL"
    return "Invalid URL"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4999, debug=True)