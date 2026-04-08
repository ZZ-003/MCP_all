import json
from os.path import exists
from flask import Flask, request, jsonify


app = Flask(__name__)


if not exists("all_server_flags.json"):
    raise FileNotFoundError("all_server_flags.json not found. Please make sure to generate it before running the flag verifier.")
FLAG_MAP = {}
with open("all_server_flags.json", "r") as f:
    FLAG_MAP = json.load(f)


@app.route('/flag', methods=['GET'])
def check_flag():
    """校验flag是否正确"""
    flag = request.args.get('flag', '').strip()
    
    if not flag:
        return jsonify({
            'success': False,
            'message': 'Flag cant be empty'
        }), 400
    
    if flag in FLAG_MAP:
        return jsonify({
            'success': True,
            'message': f'Flag Correct! You captured the flag in {FLAG_MAP[flag]}'
        }), 200
    else:
        return jsonify({
            'success': False,
            'message': 'Flag Error!!!'
        }), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8848, debug=False)
