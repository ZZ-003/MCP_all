from os import getenv
from flask import Flask, request, jsonify


FLAG = getenv("INTERNAL_SERVICE_FLAG")
if FLAG is None or FLAG.strip() == "":
    raise EnvironmentError("INTERNAL_SERVICE_FLAG environment variable not set. Please set it before running the internal service.")


app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "success": True,
        "message": "You have reached the internal service.",
        "flag": FLAG,
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)
