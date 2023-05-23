from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS, cross_origin
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = '9563dde29f7fd17d8be28464b4ae222f'
CORS(app, origins=["https://controllerfrontend.herokuapp.com/"])

app.config['MYSQL_HOST'] = 'us-cdbr-east-06.cleardb.net'
app.config['MYSQL_USER'] = 'b35dac02e83bbd'
app.config['MYSQL_PASSWORD'] = '3ab5e42d'
app.config['MYSQL_DB'] = 'heroku_31f9dde22878f1f'


mysql = MySQL(app)


@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    
    cur = mysql.connection.cursor()
    cur.execute('SELECT id, password FROM users WHERE username = %s', (username,))
    result = cur.fetchone()

    if result is None:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404
    user_id, hashed_password = result

    if not check_password_hash(hashed_password, password):
        return jsonify({'status': 'error', 'message': 'Password is incorrect'}), 400
    
    # Store the user's id in the session
    session['user_id'] = user_id
    print('user_id:', user_id)
    print('session:', session)
    return jsonify({'status': 'success', 'message': 'Logged in successfully'}), 200

@app.route('/getDeviceList', methods=['GET'])
def getDeviceList():
    # Check if the user is logged in
    
    if 'user_id' not in session:
        print('session:', session)
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    user_id = session['user_id']

    # Now use user_id to get the devices for the logged-in user
    cur = mysql.connection.cursor()
    cur.execute('SELECT device_name FROM devices WHERE user_id = %s', (user_id,))

    # Fetch all results from the cursor
    device_list = cur.fetchall()

    # Convert the tuple into a list and return
    return jsonify(list(device_list)), 200


@app.route('/getLogs', methods=['GET'])
@cross_origin()
def getLogs():
    user_id = session.get('user_id')
    if user_id is None:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
    
    cur = mysql.connection.cursor()
    
    # Fetch only logs related to the current user's devices
    cur.execute('SELECT device_log FROM devices WHERE user_id = %s', (user_id,))
    log_list = [row[0] for row in cur.fetchall()]

    return jsonify(log_list), 200

@app.route('/pages/<path:path>')
def send_static(path):
    return send_from_directory('pages', path)
    
@app.route('/addDevice', methods=['POST'])
@cross_origin()
def addDevice():
    user_id = session.get('user_id')
    if user_id is None:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
    
    device_name = request.json.get('deviceName')
    
    # Your logic to add device goes here.
    # It should add device_name to the connected devices list in your database

    cur = mysql.connection.cursor()
    cur.execute('INSERT INTO devices (user_id, device_name) VALUES (%s, %s)', (user_id, device_name))
    mysql.connection.commit()

    response = jsonify({'status': 'success', 'message': 'Device added successfully'})

    return response

