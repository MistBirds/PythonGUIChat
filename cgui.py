import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showinfo, showwarning, showerror
# askyesnocancel,askretrycancel,ask*
import socket
import json
import threading
from time import sleep, time

class SJChat():
	def __init__(self, host):
		self.interval = 6
		self.host = host
		self.socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
		self.socket.settimeout(self.interval + 1)	
		self.is_login = False
		self.receive_loop_thread = None
		self.keep_alive_thread = None
		self.username = None
		self.pre_connect_time = None
		self.time_difference = None

		self.var_user = None
		self.var_password = None
		self.var_repassword = None
		self.top = None

		self.gui_login()


	def gui_login(self):

		self.top = tk.Tk()
		self.top.title('SJChat')
		self.top.geometry('400x300')
		self.top.resizable(width=False, height=False)
		label_user = tk.Label(self.top, text='账号:', width=120, font=('宋体',16,'normal'))
		label_user.place(x=20, y=55, width=120, height=30)
		self.var_user = tk.StringVar(self.top ,value='')
		username = tk.Entry(self.top, text='', textvariable=self.var_user,  font=('宋体',16,'normal'))
		username.place(x=110, y=60, width=240, height=30)

		label_password = tk.Label(self.top, text='密码:',width=120, font=('宋体',16,'normal')) 
		label_password.place(x=20, y=105, width=120, height=30)
		self.var_password = tk.StringVar(self.top ,value='')
		password = tk.Entry(self.top, text='', textvariable=self.var_password, show='*', font=('宋体',16,'normal'))
		password.place(x=110, y=110, width=240, height=30)

		login = tk.Button(self.top, text='登陆', command=self.login, font=('宋体',16,'normal'))
		login.place(x=100, y=170, width=80)

		register = tk.Button(self.top, text='注册', command=self.gui_register, font=('宋体',16,'normal'))
		register.place(x=220, y=170, width=80)

		tk.mainloop()


	def login(self):
		username = self.var_user.get()
		password = self.var_password.get()

		self.socket.sendto(json.dumps({
			'action': 'login',
			'username': username,
			'password': password,
			}).encode(), self.host)
		
		receive_data, addr = self.socket.recvfrom(1024)
		js = json.loads(receive_data.decode())

		if js['login'] == 'success':
			showinfo('INFO', 'login success')
			self.friends = js['friends']
			self.is_login = True
			self.username = username
			self.pre_connect_time = js['time']
			self.time_difference = js['time'] - time()
			self.top.destroy()

			# is nessary?
			del self.var_password
			del self.var_user
			del self.var_repassword

			self.receive_loop_thread = threading.Thread(target=self._recive_thread)
			self.receive_loop_thread.setDaemon(True)
			self.receive_loop_thread.start()

			self.keep_alive_thread = threading.Thread(target=self._thread_keep_alive)
			self.keep_alive_thread.setDaemon(True)
			self.keep_alive_thread.start()
			self.gui_main()
		else:
			showinfo('INFO', 'login failed')


	def gui_register(self):
		self.top.destroy()
		self.top = tk.Tk()
		self.top.title('SJChat')
		self.top.geometry('400x300')
		self.top.resizable(width=False, height=False)

		label_user = tk.Label(self.top, text='账号:', width=120, font=('宋体',16,'normal'))
		label_user.place(x=20, y=55, width=120, height=30)
		self.var_user = tk.StringVar(self.top ,value='')
		username = tk.Entry(self.top, text='', textvariable=self.var_user,  font=('宋体',16,'normal'))
		username.place(x=110, y=60, width=240, height=30)

		label_password = tk.Label(self.top, text='密码:',width=120, font=('宋体',16,'normal')) 
		label_password.place(x=20, y=105, width=120, height=30)
		self.var_password = tk.StringVar(self.top ,value='')
		password = tk.Entry(self.top, text='', textvariable=self.var_password, show='*', font=('宋体',16,'normal'))
		password.place(x=110, y=110, width=240, height=30)

		label_repassword = tk.Label(self.top, text='重复密码:',width=120, font=('宋体',16,'normal')) 
		label_repassword.place(x=4, y=155, width=120, height=30)
		self.var_repassword = tk.StringVar(self.top ,value='')
		repassword = tk.Entry(self.top, text='', textvariable=self.var_repassword, show='*', font=('宋体',16,'normal'))
		repassword.place(x=110, y=160, width=240, height=30)

		register = tk.Button(self.top, text='确定注册', command=self.register, font=('宋体',16,'normal'))
		register.place(x=160, y=220, width=100)
		tk.mainloop()


	def register(self):

		username = self.var_user.get()
		password = self.var_password.get()
		repassword = self.var_repassword.get()
		
		if username == '' or username == None:
			showwarning('Warning', 'username must be not None')
			return None
		elif password == '' or password == None:
			showwarning('Warning', 'password must be not None')
			return None
		if password != repassword:
			showerror('Error', 'password and repassword not equal')
			return None

		self.socket.sendto(json.dumps({
			'action': 'register',
			'username': username,
			'password': password,
			}).encode(), self.host)

		receive_data, addr = self.socket.recvfrom(1024)
		js = json.loads(receive_data.decode())
		if js['register'] == 'success':
			showinfo('INFO', 'register success')
			self.top.destroy()
			self.gui_login()
		else:
			showinfo('INFO', 'register failed')


	def _thread_keep_alive(self):
		while self.is_login:
			sleep(self.interval)
			self.socket.sendto(json.dumps({
				'action': 'update_timestamp',
				'username': self.username,
				}).encode(), self.host)
			if abs(time() + self.time_difference - \
				self.pre_connect_time) > 2*self.interval:
				self.is_login = False
				self.top.title("SJChat %s-offline" % self.username)

	def _recive_thread(self):
		while self.is_login:
			receive_data, addr = self.socket.recvfrom(1024)
			js = json.loads(receive_data.decode())

			# 判断服务器发来的消息类型
			if 'action' in js.keys():
				if js['action'] == 'is_online':
					self.pre_connect_time = js['time']
				elif js['action'] == 'userlist':
					print('userlist:', js['userlist'])
				elif js['action'] == 'sendmessage':
					print('%s: %s' % (js['sender'], js['message']))


	# def get_friend_list(self):
	# 	self.socket.sendto(json.dumps({
	# 		'action': 'get_friend_list',
	# 		'username': username,
	# 		}).encode(), self.host)

	def gui_main(self):
		self.top = tk.Tk()
		self.top.title("SJChat %s" % self.username)
		self.top.geometry('320x600')
		self.top.resizable(width=False, height=False)
		
		# friend list
		self.scrollbar = tk.Scrollbar(self.top)
		self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
		title = ['1','2','3']
		self.box = ttk.Treeview(self.top, columns=title,
			yscrollcommand=self.scrollbar.set, height='20',
			show='headings')

		self.box.column('1', width=80, anchor='w')
		self.box.column('2', width=150, anchor='w')
		self.box.column('3', width=35, anchor='w')

		self.box.heading('1', text='昵称')
		self.box.heading('2', text='简介')
		self.box.heading('3', text='状态')
		for i in self.friends:
			self.box.insert('','end',values=i)
		self.scrollbar.config(command=self.box.yview)
		self.box.pack()

		# action menu
		self.addfriend = tk.Button(self.top, text='添加好友', command=None, font=('宋体',14,'normal'))
		self.addfriend.place(x=50, y=480, width=90)

		self.modify_info = tk.Button(self.top, text='修改签名', command=None, font=('宋体',14,'normal'))
		self.modify_info.place(x=160, y=480, width=90)

		tk.mainloop()


t = SJChat(('127.0.0.1', 12346))
