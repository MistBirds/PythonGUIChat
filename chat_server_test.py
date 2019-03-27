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
			self.cursor.execute('CREATE TABLE users(username varchar(16) PRIMARY KEY,\
				password varchar(16), userinfo varchar(100), nickname varchar(16), \
				sex varchar(6) check (sex in ("男","女")))')
			self.cursor.execute('CREATE TABLE friends(username varchar(16),\
				friend varchar(16), CONSTRAINT pk PRIMARY KEY(username,friend))')
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
			'update_profile': self.client_update_profile,
			'find_friends': self.client_find_friends,
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
			self.cursor.execute('INSERT INTO users values("%s","%s","%s","%s","%s")' % 
				(js['username'],js['password'],js['info'],js['nickname'],'男' if js['sex'] == 0 else '女'))
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
		self.cursor.execute('SELECT password,userinfo,nickname,sex FROM users WHERE username="%s"' % js['username'])
		res = self.cursor.fetchone()
		# 登陆失败
		if (res == None or res[0] != js['password']) or (js['username'] in self.user_list):
			self.socket.sendto(json.dumps({
				'login': 'failure',
				}).encode(), client_addr)
		# 登陆成功
		elif res[0] == js['password']:
			friends = self.get_user_friend(js['username'])
			self.socket.sendto(json.dumps({
				'login': 'success',
				'time': time(),
				'profile': {'userinfo': res[1], 'nickname': res[2], 'sex': res[3]},
				'friends': friends,
				}).encode(), client_addr)
			# 登陆成功后添加在线列表
			user_info = [client_addr, time()]
			self.user_list[js['username']]=user_info


	def client_update_timestamp(self, js, client_addr):
		if js['username'] in self.user_list:
			self.user_list[js['username']][1] = time()
			self.socket.sendto(json.dumps({
				'action': 'is_online',
				'time': time(),
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


	def client_update_profile(self, js, client_addr):
		if js['nickname'] != '' and js['nickname'] != None:
			if js['sex'] in (0,1):
				self.cursor.execute('UPDATE users SET userinfo="%s", nickname="%s", sex="%s" WHERE username="%s"' %
					(js['info'], js['nickname'], '男' if js['sex'] == 0 else '女', js['username']))
				self.db.commit()

				profile = {'nickname': js['nickname'],'userinfo': js['info'],
					'sex': '男' if js['sex'] == 0 else '女'}

				self.socket.sendto(json.dumps({
					'action': 'update_profile_ok',
					'profile': profile,
					}).encode(), client_addr)

	def client_find_friends(self, js, client_addr):
		if js['type'] == 'by_username':
			self.cursor.execute('SELECT username, nickname, userinfo, sex\
			 FROM users WHERE username="%s"' % js['username'])
			res = self.cursor.fetchone()
			if res != None:
				self.socket.sendto(json.dumps({
					'action': 'res_of_find_friends',
					'friends': res,
					}).encode(), client_addr)
		elif js['type'] == 'by_nickname':
			self.cursor.execute('SELECT username, nickname, userinfo, sex\
			 FROM users WHERE nickname="%s"' % js['nickname'])
			res = self.cursor.fetchall()
			if res != None:
				self.socket.sendto(json.dumps({
					'action': 'res_of_find_friends',
					'friends': res,
					}).encode(), client_addr)
		

	def get_user_friend(self, username):
		friend_list = []
		self.cursor.execute('SELECT friend FROM friends WHERE username="%s"' % username)
		res = self.cursor.fetchall()
		for i in res:
			t = []
			t.append(i[0])
			self.cursor.execute('SELECT userinfo FROM users WHERE username="%s"' % i[0])
			t.append(self.cursor.fetchone()[0])
			if i[0] in self.user_list:
				t.append('在线')
			else:
				t.append('离线')
			friend_list.append(t)
		# return [['bird', 'let it go', '在线'], ['u1', 'df', '离线']]
		return friend_list


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
