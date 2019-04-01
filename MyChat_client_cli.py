import socket
import json
import threading
from cmd import Cmd
from time import sleep

class Client(Cmd):
	"""python socket chat client"""
	prompt = '>>>'
	intro = '[Welcome] 简易聊天室客户端(Cli版)'
	buffersize = 1024

	def __init__(self, host):
		super().__init__()
		self.socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
		self.host = host
		self.receive_loop_thread = None
		self.is_login = False
		self.username = None
		self.interval = 6
		self.keep_alive_thread = None

		self.socket.settimeout(self.interval + 1)

	def __recive_thread(self):
		while self.is_login:
			receive_data, addr = self.socket.recvfrom(1024)
			js = json.loads(receive_data.decode())

			# 判断服务器发来的消息类型
			if 'action' in js.keys():
				if js['action'] == 'userlist':
					print('userlist:', js['userlist'])

				if js['action'] == 'sendmessage':
					print('%s: %s' % (js['sender'], js['message']))

		

	def do_sendto(self, args):
		try:
			acceptor = args.split(' ')[0]
			message = args.split(' ')[1]
		except:
			print('Useage: sendto acceptor message')
			return

		self.socket.sendto(json.dumps({
			'action': 'sendmessage',
			'message': message,
			'acceptor': acceptor,
			'username': self.username,
			}).encode(), self.host)



	# 注册账号
	def do_register(self, args):
		try:
			username = args.split(' ')[0]
			password = args.split(' ')[1]
		except:
			print('Useage: register username password')
			return

		self.socket.sendto(json.dumps({
			'action': 'register',
			'username': username,
			'password': password,
			}).encode(), self.host)

		receive_data, addr = self.socket.recvfrom(1024)
		js = json.loads(receive_data.decode())
		if js['register'] == 'success':
			print('INFO: register successful!')
		else:
			print('INFO: register failed!')


	def do_login(self, args):
		if self.is_login == True:
			print('you are logged')
			return
		try:
			username = args.split(' ')[0]
			password = args.split(' ')[1]
		except:
			print('Useage: login username password')
			return

		self.socket.sendto(json.dumps({
			'action': 'login',
			'username': username,
			'password': password,
			}).encode(), self.host)
		
		receive_data, addr = self.socket.recvfrom(1024)
		js = json.loads(receive_data.decode())

		if js['login'] == 'success':
			print('INFO: login success')
			self.is_login = True
			self.username = username
			self.receive_loop_thread = threading.Thread(target=self.__recive_thread)
			self.receive_loop_thread.setDaemon(True)
			self.receive_loop_thread.start()

			self.keep_alive_thread = threading.Thread(target=self._thread_keep_alive)
			self.keep_alive_thread.setDaemon(True)
			self.keep_alive_thread.start()
		else:
			print('INFO: login failed')


	def start(self):
		self.cmdloop()

	def do_exit(self, args):  # 以do_*开头为命令
		self.socket.sendto(json.dumps({
			'action': 'exit',
			'username': self.username,
			}).encode(), self.host)
		self.is_login = False

		print("Exit")
		exit(0)


	def do_userlist(self, arg):
		if self.is_login:
			self.socket.sendto(json.dumps({
				'action': 'userlist',
				}).encode(), self.host)
		else:
			print('you should login first')


	def _thread_keep_alive(self):
		while self.is_login:
			try:
				sleep(self.interval)
				self.socket.sendto(json.dumps({
					'action': 'update_timestamp',
					'username': self.username,
					}).encode(), self.host)
			except:
				print('cannot connect the host')


c = Client(('127.0.0.1', 12346))
c.start()