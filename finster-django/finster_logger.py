#!/usr/bin/python
import zmq  
from datetime import datetime
import MySQLdb
import json

socket = zmq.Context().socket(zmq.SUB) 
socket.bind("tcp://127.0.0.1:5556")
socket.setsockopt(zmq.SUBSCRIBE, "")

conn = MySQLdb.connect(host = "localhost",
                       user = "finsterlogs",
                       passwd = "f1nst3r123",
                       db = "finsterlogs")

while True:  
	try:
		msg = socket.recv()  
		data = json.loads(msg)
		entry_ts = data['entry_ts']
		msg = data['message']
		userid = data['userid']
		api_call = data['api_call']
		cursor = conn.cursor()
		cursor.execute("insert into log(entry_ts,entry,user_id,api_call) values ('%s', '%s', %ld, '%s')" % (entry_ts, msg, userid, api_call))
		conn.commit()
	except Exception as e:
		print e
