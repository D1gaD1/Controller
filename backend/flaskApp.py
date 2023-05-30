import os
import redis
from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS, cross_origin
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash
from flask_session import Session
import paho.mqtt.client as mqtt


app = Flask(__name__)
app.secret_key = '9563dde29f7fd17d8be28464b4ae222f'
CORS(app, resources={r"/*": {"origins": "https://controllerfrontend.herokuapp.com"}}, supports_credentials=True)
app.config['MYSQL_HOST'] = 'us-cdbr-east-06.cleardb.net'
app.config['MYSQL_USER'] = 'b35dac02e83bbd'
app.config['MYSQL_PASSWORD'] = '3ab5e42d'
app.config['MYSQL_DB'] = 'heroku_31f9dde22878f1f'
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url(os.getenv('REDISCLOUD_URL'))
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True
app.debug = True
Session(app)

mysql = MySQL(app)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST') # Add any other methods you need
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response


@app.route('/login', methods=['POST', 'OPTIONS'])
@cross_origin()
def login():
    if request.method == 'OPTIONS':
        # Prepare response for the preflight request
        response = app.make_default_options_response()

        # Allow the actual request's methods and headers
        headers = response.headers
        headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    username = request.json.get('username')
    password = request.json.get('password')
    
    cur = mysql.connection.cursor()
    cur.execute('SELECT UID, password FROM users WHERE username = %s', (username,))
    result = cur.fetchone()

    if result is None:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404
    user_id, hashed_password = result

    if not check_password_hash(hashed_password, password):
        return jsonify({'status': 'error', 'message': 'Password is incorrect'}), 400
    
    # Store the user's id in the session
    session['user_id'] = user_id
    print(session)

    # Get controllers
    controllers = getControllerList(user_id)

    return jsonify({'status': 'success', 'message': 'Logged in successfully', 'controllers': controllers}), 200

def getControllerList(user_id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT con_name FROM controller WHERE UID = %s', (user_id,))
    controller_list = [row[0] for row in cur.fetchall()]
    return controller_list

@app.route('/getControllerDevices', methods=['POST'])
@cross_origin()
def getControllerDevices():
    print(session)
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    user_id = session['user_id']
    controller_name = request.json.get('controllerName')
    
    cur = mysql.connection.cursor()
    cur.execute('SELECT name FROM devices WHERE CID = (SELECT CID FROM controller WHERE UID = %s AND con_name = %s)', (user_id, controller_name))

    device_list = [row[0] for row in cur.fetchall()]

    return jsonify(device_list), 200

@app.route('/getDeviceDetails', methods=['POST'])
@cross_origin()
def getDeviceDetails():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    user_id = session['user_id']
    device_name = request.json.get('deviceName')
    
    cur = mysql.connection.cursor()
    cur.execute('SELECT name, hesh, ctrl FROM devices WHERE CID IN (SELECT CID FROM controller WHERE UID = %s) AND name = %s', (user_id, device_name))

    device_detail = cur.fetchone()

    if device_detail is None:
        return jsonify({'status': 'error', 'message': 'Device not found'}), 404

    device_info = {
        'name': device_detail[0],
        'hesh': device_detail[1],
        'ctrl': device_detail[2]
    }

    return jsonify(device_info), 200


@app.route('/getDeviceList', methods=['POST'])
@cross_origin()
def getDeviceList():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    user_id = session['user_id']

    cur = mysql.connection.cursor()
    cur.execute('''
                SELECT d.name, d.info, c.command, c.com_info
                FROM devices d
                INNER JOIN dev_com dc ON d.DID = dc.DID
                INNER JOIN commands c ON dc.ComID = c.ComID
                WHERE d.CID IN (SELECT CID FROM controller WHERE UID = %s)
                ''', (user_id,))

    rows = cur.fetchall()

    device_list = {}
    for row in rows:
        device_name, device_info, command, com_info = row
        if device_name not in device_list:
            device_list[device_name] = {'name': device_name, 'info': device_info, 'commands': []}
        device_list[device_name]['commands'].append({'command': command, 'com_info': com_info})

    return jsonify(list(device_list.values())), 200

@app.route('/updateCommandInfo', methods=['POST'])
@cross_origin()
def updateCommandInfo():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    user_id = session['user_id']
    device_name = request.json.get('deviceName')
    command = request.json.get('command')
    new_com_info = request.json.get('newComInfo')
    
    try:
        cur = mysql.connection.cursor()
        cur.execute('''
                    UPDATE commands c
                    INNER JOIN dev_com dc ON c.ComID = dc.ComID
                    INNER JOIN devices d ON dc.DID = d.DID
                    SET c.com_info = %s
                    WHERE d.name = %s AND c.command = %s AND d.CID IN (SELECT CID FROM controller WHERE UID = %s)
                    ''',
                    [new_com_info, device_name, command, user_id])

        # Commit changes and close cursor
        mysql.connection.commit()
        cur.close()

        return jsonify({'status': 'success'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Failed to update command info: ' + str(e)}), 500


@app.route('/getLogs/<controllerName>', methods=['POST'])
@cross_origin()
def getLogs(controllerName):
    cur = mysql.connection.cursor()
    
    # Fetch only logs related to the specified controller
    cur.execute('SELECT log FROM controller WHERE con_name = %s', (controllerName,))
    log_list = [row[0] for row in cur.fetchall()]

    return jsonify(log_list), 200


@app.route('/getCommand/<name>/<command>', methods=['GET'])
def get_command(name, command):
    # Get the device hash from the database
    cur = mysql.connection.cursor()
    cur.execute('SELECT hesh FROM devices WHERE name = %s', (name,))
    row = cur.fetchone()
    print(command)
    print(name)
    if row is None:
        return jsonify({'status': 'error', 'message': 'Device not found'}), 404

    device_hash = row[0]
    print(command)
    print(device_hash)

    # Create an MQTT client and connect to the broker
    client = mqtt.Client("Backend")  # It's good practice to give your client a unique name
    #client.username_pw_set("opilane", "Passw0rd")
    client.connect("192.168.8.69", 1883, 60)

    client.loop_start()

    # Publish the command
    topic = f"zigbee2mqtt/{device_hash}/set"
    payload = command
    print(topic, payload)
    client.publish(topic, payload)

    client.loop_stop()
    client.disconnect()

    return jsonify({'status': 'success', 'message': 'Command sent successfully'}), 200





    #return jsonify({'command': 'mosquitto_pub -t \'zigbee2mqtt/0xdc8e95fffe090c17/set\' -m \'{ "state": "TOGGLE" }\''})

    
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

@app.route('/updateDeviceInfo', methods=['POST'])
@cross_origin()
def updateDeviceInfo():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    user_id = session['user_id']
    old_device_name = request.json.get('oldDeviceName')
    new_device_name = request.json.get('newDeviceName')
    device_info = request.json.get('deviceInfo')
    
    try:
        cur = mysql.connection.cursor()
        cur.execute('UPDATE devices SET name = %s, info = %s WHERE name = %s AND CID IN (SELECT CID FROM controller WHERE UID = %s)',
                    [new_device_name, device_info, old_device_name, user_id])

        # Commit changes and close cursor
        mysql.connection.commit()
        cur.close()

        return jsonify({'status': 'success'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Failed to update device info: ' + str(e)}), 500

