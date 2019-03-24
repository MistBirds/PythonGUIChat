import tkinter as tk
from tkinter.messagebox import showinfo, showwarning, showerror
import socket
import json
import threading

class SJChat():
	def __init__(self, host):
		self.socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
		self.host = host
		self.var_user = None
		self.var_password = None
		self.var_repassword = None
		self.is_login = False
		self.receive_loop_thread = None
		self.keep_alive_thread = None
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
			self.is_login = True
			self.username = username
			self.top.destroy()

			# is nessary?
			del self.var_password
			del self.var_user
			del self.top
			del self.var_repassword

			# self.receive_loop_thread = threading.Thread(target=self.__recive_thread)
			# self.receive_loop_thread.setDaemon(True)
			# self.receive_loop_thread.start()

			# self.keep_alive_thread = threading.Thread(target=self._thread_keep_alive)
			# self.keep_alive_thread.setDaemon(True)
			# self.keep_alive_thread.start()
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


t = SJChat(('127.0.0.1', 12346))
