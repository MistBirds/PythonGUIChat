import json
import socket
import sqlite3
from os import path
from time import time, sleep
import threading
		

class ChatServer():
	''' python socket chat server'''

	def __init__(self, port):
		self.user_list = {}
		self.port = port
		self.interval = 6
		self.timeout = 7

	def run(self):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.socket.bind(('127.0.0.1', self.port))
		if not path.exists('chat.db'):
			self.db = sqlite3.connect('chat.db')
			self.cursor = self.db.cursor()
			self.cursor.execute('CREATE TABLE users(username varchar(16),\
				password varchar(16))')
		else:
			self.db = sqlite3.connect('chat.db')
			self.cursor = self.db.cursor()
		print('server initial on port %s...' % self.port)

		# start _thread_online_judge
		jt = threading.Thread(target=self._thread_online_judge)
		# jt.setDaemon(True)
		jt.start()

		actions = {
			'register': self.client_register,
			'login': self.client_login,
			'update_timestamp': self.client_update_timestamp,
			'exit': self.client_exit,
			'userlist': self.client_userlist,
			'sendmessage': self.client_sendmessage,
			}

		while True:
			try:
				receive_data, client_addr = self.socket.recvfrom(1024)
				js = json.loads(receive_data.decode())
				# execute action to response the request
				action = actions[js['action']]
				action(js, client_addr)
					
			except Exception as e:
				print('error: ',e)
				exit(1)

	def client_exit(self, js, client_addr):
		if js['username'] in self.user_list:
			self.user_list.pop(js['username'])


	def client_register(self, js, client_addr):
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


	def client_login(self, js, client_addr):
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
			user_info = [client_addr, time()]
			self.user_list[js['username']]=user_info


	def client_update_timestamp(self, js, client_addr):
		if js['username'] in self.user_list:
			self.user_list[js['username']][1] = time()
			self.socket.sendto(json.dumps({
				'isonline': 'yes',
				}).encode(), client_addr)
		else:
			self.socket.sendto(json.dumps({
				'isonline': 'no',
				}).encode(), client_addr)


	def client_userlist(self, js, client_addr):
		self.socket.sendto(json.dumps({
			'action': 'userlist',
			'userlist': self.user_list,
			}).encode(), client_addr)


	def client_sendmessage(self, js, client_addr):
		if js['acceptor'] in self.user_list:
			self.socket.sendto(json.dumps({
				'action': 'sendmessage',
				'message': js['message'],
				'sender': js['username'],
				}).encode(), self.user_list[js['acceptor']][0])

	def _thread_online_judge(self):
		while True:
			sleep(self.interval)
			t = time()
			pop_list = []
			# find the user who has timeout
			for i in self.user_list.keys():
				if t - self.user_list[i][1] > self.timeout:
					pop_list.append(i)
			# pop the user who has timeout
			for i in pop_list:
				self.user_list.pop(i)
	
	def start(self):
		# start main thread as a daemon
		mt = threading.Thread(target=self.run)
		mt.setDaemon(True)
		mt.start()

		while True:
			x = input()
			if x == '1':
				print(self.user_list)
			if x == '0':
				exit(0)


def main():
	server = ChatServer(12346)
	server.start()

if __name__ == '__main__':
	main()
