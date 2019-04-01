import json
import socket
import sqlite3
from os import path
from time import time, sleep
import threading
import traceback
		

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
			# create table users for save users info
			self.cursor.execute('CREATE TABLE users(username varchar(16) PRIMARY KEY,\
				password varchar(16), userinfo varchar(100), nickname varchar(16), \
				sex varchar(6) check (sex in ("男","女")))')
			# create table friends to save the relationship of two users
			self.cursor.execute('CREATE TABLE friends(username varchar(16),\
				friend varchar(16), CONSTRAINT pk PRIMARY KEY(username,friend))')
			# create table add_friend_request for save the request which can not execute right now
			self.cursor.execute('CREATE TABLE add_friend_request(requested varchar(16), \
				sender varchar(16), request_time varchar(20), is_processed int(1))')
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
			'add_friend': self.client_add_friend,
			'add_friend_ok': self.client_add_friend_ok,
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
				traceback.print_exc()
				exit(1)

	def client_exit(self, js, client_addr):
		if js['username'] in self.user_list:
			self.user_list.pop(js['username'])
			friends = self.get_user_friend(js['username'])
			self.logout_inform(friends, js['username'])


	def client_register(self, js, client_addr):
		self.cursor.execute('SELECT count(*) FROM users WHERE username="%s"' % js['username'])
		res = self.cursor.fetchone()
		# Registered success
		if res[0] == 0:
			self.cursor.execute('INSERT INTO users values("%s","%s","%s","%s","%s")' % 
				(js['username'],js['password'],js['info'],js['nickname'],'男' if js['sex'] == 0 else '女'))
			self.db.commit()
			self.socket.sendto(json.dumps({
				'register': 'success',
				}).encode(), client_addr)
		# Registration failure
		else:
			self.socket.sendto(json.dumps({
				'register': 'failure',
				}).encode(), client_addr)


	def client_login(self, js, client_addr):
		self.cursor.execute('SELECT password,userinfo,nickname,sex FROM users\
		 WHERE username="%s"' % js['username'])
		res = self.cursor.fetchone()
		# 登陆失败
		if (res == None or res[0] != js['password']) or (js['username'] in self.user_list):
			self.socket.sendto(json.dumps({
				'login': 'failure',
				}).encode(), client_addr)
		# 登陆成功
		elif res[0] == js['password']:
			# 获取好友列表
			friends = self.get_user_friend(js['username'])
			# 发送好友列表
			self.socket.sendto(json.dumps({
				'login': 'success',
				'time': time(),
				'profile': {'userinfo': res[1], 'nickname': res[2], 'sex': res[3]},
				'friends': friends,
				}).encode(), client_addr)
			# 通知在线好友上线消息
			self.login_inform(friends, js['username'])
			# 登陆成功后添加在线列表
			user_info = [client_addr, time()]
			self.user_list[js['username']]=user_info

			sleep(3)
			# 获取未处理好友申请列表
			self.cursor.execute('SELECT requested, sender, request_time FROM \
				add_friend_request WHERE requested="%s" and is_processed=0' % js['username'])
			add_friend_requests = self.cursor.fetchall()
			for item in add_friend_requests:
				self.socket.sendto(json.dumps({
					'action': 'add_friend_request',
					'friendname': item[1],
					'request_time': item[2],
					}).encode(), client_addr)
			self.cursor.execute('UPDATE add_friend_request SET is_processed=1 WHERE requested="%s"' % js['username'])


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


	def client_add_friend(self, js, client_addr):
		if js['friendname'] in self.user_list:
			self.socket.sendto(json.dumps({
				'action': 'add_friend_request',
				'friendname': js['username'],
				'request_time': js['request_time']
				}).encode(), self.user_list[js['friendname']][0])
		else:
			# save the add_friend request on database
			self.cursor.execute('INSERT INTO add_friend_request VALUES("%s","%s","%s",0)' % (js['friendname'], 
				js['username'], js['request_time']))
			self.db.commit()

	def client_add_friend_ok(self, js, client_addr):
		res = self.cursor.execute('SELECT username,friend FROM friends WHERE username="%s" \
			and friend="%s"' % (js['username'], js['friendname'])).fetchone()
		if res == None:
			self.cursor.execute('INSERT INTO friends VALUES("%s","%s")' % (js['username'], js['friendname']))
			self.cursor.execute('INSERT INTO friends VALUES("%s","%s")' % (js['friendname'], js['username']))
			self.db.commit()
			# update two user friends list
			self.socket.sendto(json.dumps({
				'action': 'update_friends',
				'friends': self.get_user_friend(js['username']),
				}).encode(), client_addr)
			if js['friendname'] in self.user_list:
				self.socket.sendto(json.dumps({
					'action': 'update_friends',
					'friends': self.get_user_friend(js['friendname']),
					}).encode(), self.user_list[js['friendname']][0])


	def login_inform(self, friends, username):
		'''After landing successfully, inform your online friends'''
		for friend in friends:
			if friend[0] in self.user_list.keys():
				self.socket.sendto(json.dumps({
					'action': 'login_inform',
					'username': username,
					}).encode(), self.user_list[friend[0]][0])


	def logout_inform(self,friends, username):
		'''After logout, inform your online friends'''
		for friend in friends:
			if friend[0] in self.user_list.keys():
				self.socket.sendto(json.dumps({
					'action': 'logout_inform',
					'username': username,
					}).encode(), self.user_list[friend[0]][0])
		

	def get_user_friend(self, username):
		friend_list = []
		self.cursor.execute('SELECT friend FROM friends WHERE username="%s"' % username)
		res = self.cursor.fetchall()
		for i in res:
			t = []
			self.cursor.execute('SELECT nickname,userinfo FROM users WHERE username="%s"' % i[0])
			tt = self.cursor.fetchone()
			t.append(i[0]) # username
			t.append(tt[0])	# nickname
			t.append(tt[1])	# userinfo
			if i[0] in self.user_list:
				t.append('在线')
			else:
				t.append('离线')
			friend_list.append(t)
		# return [['ubird','bird', 'let it go', '在线'], ['uu1','u1', 'df', '离线']]
		return friend_list


	def _thread_online_judge(self):
		db = sqlite3.connect('chat.db')
		cursor = db.cursor()
		
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
				cursor.execute('SELECT friend FROM friends WHERE username="%s"' % i)
				res = cursor.fetchall()
				self.logout_inform(res, i)
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
