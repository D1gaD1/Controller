import os 
import time 
import requests
import json 
import mysql.connector 

def send_command(command): 
    print(f"Executing command: {command}") 
    result = os.system(command) 
    if result != 0:  
        print("Error occurred.")
        return None
    return result 

def get_next_command(): 
    response = requests.get('https://controllerbackend.herokuapp.com/getCommand') 
    command = response.json().get('command')
    return command 

def send_output_to_db(output, device_id): 
    cnx = mysql.connector.connect(user='b35dac02e83bbd', password='3ab5e42d', host='us-cdbr-east-06.cleardb.net', database='heroku_31f9dde22878f1f') 
    cursor = cnx.cursor() 
    add_output = "UPDATE controller SET log=%s WHERE CID = %s"
    data_output = (output, device_id)
    cursor.execute(add_output, data_output) 
    cnx.commit() 
    cursor.close() 
    cnx.close() 

while True: 
    command = get_next_command() 
    if command:   
        output = send_command(command) 
        if output is not None: 
            send_output_to_db(output, device_id)
    time.sleep(5) 

send_command("sudo systemctl start zigbee2mqtt") 
#send_command("mosquitto_pub -t 'zigbee2mqtt/0xdc8e95fffe090c17/set' -m '{ \"state\": \"TOGGLE\" }'")
