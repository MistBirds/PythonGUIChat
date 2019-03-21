import json
import socket
import sqlite3
from os import path
from time import ctime
		

class ChatServer():
	''' python socket chat server'''

	def __init__(self, port):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.socket.bind(('127.0.0.1', port))
		if not path.exists('chat.db'):
			self.db = sqlite3.connect('chat.db')
			self.cursor = self.db.cursor()
			self.cursor.execute('CREATE TABLE users(username varchar(16),\
				password varchar(16))')
		else:
			self.db = sqlite3.connect('chat.db')
			self.cursor = self.db.cursor()

		self.addr_list = []
		self.user_list = []

		print('server initial on port %s...' % port)

	def run(self):
		while True:
			try:
				receive_data, client_addr = self.socket.recvfrom(1024)
				js = json.loads(receive_data.decode())

				# 注册
				if js['action'] == 'register':
					self.cursor.execute('SELECT count(*) FROM users WHERE username="%s"' % js['username'])
					res = self.cursor.fetchone()
					# 成功注册
					if res[0] == 0:
						self.cursor.execute('INSERT INTO users values("%s","%s")' % (js['username'],js['password']))
						self.db.commit()
						self.socket.sendto(json.dumps({
							'register': 'success',
							}).encode(), client_addr)
					# 注册失败
					else:
						self.socket.sendto(json.dumps({
							'register': 'failure',
							}).encode(), client_addr)

				# 登陆
				elif js['action'] == 'login':
					self.cursor.execute('SELECT password FROM users WHERE username="%s"' % js['username'])
					res = self.cursor.fetchone()
					# 登陆失败
					if res == None or res[0] != js['password']:
						self.socket.sendto(json.dumps({
							'login': 'failure',
							}).encode(), client_addr)
					# 登陆成功
					elif res[0] == js['password']:
						self.socket.sendto(json.dumps({
							'login': 'success',
							}).encode(), client_addr)
						# 登陆成功后添加在线列表
						self.addr_list.append((client_addr, ctime()))
						self.user_list.append(js['username'])
					
			except Exception as e:
				print('error: ',e)
				exit(1)
	
	def start(self):
		self.run()


def main():
	server = ChatServer(12346)
	server.start()

if __name__ == '__main__':
	main()
