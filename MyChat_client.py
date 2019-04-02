import tkinter as tk
from tkinter import ttk,IntVar,StringVar
from tkinter.messagebox import showinfo, showwarning, showerror, askokcancel
# askyesno,askretrycancel,ask*
import socket
import json
import threading
from time import sleep, time, ctime
import re

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
		self.profile = None
		self.pre_connect_time = None
		self.time_difference = None
		self.box = None
		self.find_user_box = None
		self.friends = None  # main friends list
		self.selected_furture_friend = None
		self.sys_messages_count = 0
		self.var_sys_messages = None
		self.system_message = []
		self.sys_message_box = None
		# _recive_thread provided data to gui_add_friend
		self.res_of_find_friends = []

		self.var_user = None
		self.var_password = None
		self.var_repassword = None
		self.var_nickname = None

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
			self.friends = js['friends']  # like [['ubird','bird', 'let it go', '在线'], ['uu1','u1', 'df', '离线']]
			self.is_login = True
			self.username = username
			self.pre_connect_time = js['time']
			self.time_difference = js['time'] - time()
			self.top.destroy()
			self.profile = js['profile']
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
		self.top.geometry('400x540')
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

		label_nickname = tk.Label(self.top, text='昵称:',width=120, font=('宋体',16,'normal')) 
		label_nickname.place(x=20, y=205, width=120, height=30)
		self.var_nickname = tk.StringVar(self.top ,value='')
		nickname = tk.Entry(self.top, text='', textvariable=self.var_nickname, font=('宋体',16,'normal'))
		nickname.place(x=110, y=210, width=240, height=30)

		label_info = tk.Label(self.top, text='个性签名:',width=120, font=('宋体',16,'normal')) 
		label_info.place(x=4, y=255, width=120, height=30)
		self.info = tk.Text(self.top, width=22, height=6,font=('宋体',16,'normal'))
		self.info.place(x=110, y=260)

		label_info = tk.Label(self.top, text='性别:',width=120, font=('宋体',16,'normal')) 
		label_info.place(x=20, y=420, width=120, height=30)
		self.sex = IntVar()
		self.sex.set(0)
		rbtn_sex1 = tk.Radiobutton(self.top, variable=self.sex, text='男', value=0)
		rbtn_sex1.place(x=140, y=425)
		rbtn_sex2 = tk.Radiobutton(self.top, variable=self.sex, text='女', value=1)
		rbtn_sex2.place(x=250, y=425)

		register = tk.Button(self.top, text='确定注册', command=self.register, font=('宋体',16,'normal'))
		register.place(x=160, y=460, width=100)
		tk.mainloop()


	def register(self):

		username = self.var_user.get()
		password = self.var_password.get()
		repassword = self.var_repassword.get()
		nickname = self.var_nickname.get()
		info = self.info.get(0.0,tk.END)
		sex = self.sex.get()

		if username == '' or username == None:
			showwarning('Warning', 'username must be not None')
			return None
		elif password == '' or password == None:
			showwarning('Warning', 'password must be not None')
			return None
		if password != repassword:
			showerror('Error', 'password and repassword not equal')
			return None
		
		if nickname == '' or nickname == None:
			showwarning('Warning', 'nickname must be not None')
			return None


		self.socket.sendto(json.dumps({
			'action': 'register',
			'username': username,
			'password': password,
			'nickname': nickname,
			'info': info,
			'sex': sex,
			}).encode(), self.host)

		receive_data, addr = self.socket.recvfrom(1024)
		js = json.loads(receive_data.decode())
		if js['register'] == 'success':
			showinfo('INFO', 'register success')
			self.top.destroy()
			self.gui_login()
		else:
			showinfo('INFO', 'register failed')


	def gui_add_friend(self):
		if not self.is_login:
			return

		self.selected_furture_friend = None

		x = tk.Tk()
		x.title('SJChat add friend')
		x.geometry('360x520')
		x.resizable(width=False, height=False)

		var_friend_username = tk.StringVar(x ,value='')
		var_friend_nickname = tk.StringVar(x ,value='')

		label_invisible0 = tk.Label(x, text='')
		label_invisible0.pack()

		label_username = tk.Label(x, text='账户查找', font=('宋体', 16, 'normal'))
		label_username.pack()

		entry_friend_username = tk.Entry(x, text='', textvariable=var_friend_username,
		 font=('宋体', 16, 'normal'))
		entry_friend_username.pack()

		btn_find_by_username = tk.Button(x, text='账户查找', command=lambda: self.find_by_username(
			var_friend_username.get(), var_friend_nickname), font=('宋体', 16, 'normal'))
		btn_find_by_username.pack()

		label_invisible1 = tk.Label(x, text='')
		label_invisible1.pack()

		label_nickname = tk.Label(x, text='昵称查找', font=('宋体', 16, 'normal'))
		label_nickname.pack()

		entry_friend_nickname = tk.Entry(x, text='', textvariable=var_friend_nickname, 
			font=('宋体', 16, 'normal'))
		entry_friend_nickname.pack()

		btn_add = tk.Button(x, text='昵称查找', command=lambda: self.find_by_nickname(
			var_friend_nickname.get(),var_friend_username), font=('宋体', 16, 'normal'))
		btn_add.pack()

		label_invisible2 = tk.Label(x, text='')
		label_invisible2.pack()

		# result list
		scrollbar = tk.Scrollbar(x)
		scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
		title = ['0','1','2','3']
		self.find_user_box = ttk.Treeview(x, columns=title,
			yscrollcommand=scrollbar.set, height='8',
			show='headings')

		self.find_user_box.column('0', width=80, anchor='w')
		self.find_user_box.column('1', width=80, anchor='w')
		self.find_user_box.column('2', width=150, anchor='w')
		self.find_user_box.column('3', width=35, anchor='w')

		self.find_user_box.heading('0', text='账号')
		self.find_user_box.heading('1', text='昵称')
		self.find_user_box.heading('2', text='简介')
		self.find_user_box.heading('3', text='性别')

		scrollbar.config(command=self.find_user_box.yview)
		self.find_user_box.pack()

		label_invisible3 = tk.Label(x, text='')
		label_invisible3.pack()

		btn_makesure_add = tk.Button(x, text='确认添加', command=self.click_makesure_add, font=('宋体', 16, 'normal'))
		btn_makesure_add.pack()

		self.find_user_box.bind('<ButtonRelease-1>', self.click_friendlist)


	def find_by_username(self,username,var_friend_nickname):
		# clear nickname
		var_friend_nickname.set("")
		# clear the list
		items = self.find_user_box.get_children()
		for item in items:
			self.find_user_box.delete(item)
		# clear self.res_of_find_friends
		self.res_of_find_friends.clear()

		# sent request to server for looking user by username
		self.socket.sendto(json.dumps({
			'action': 'find_friends',
			'type': 'by_username',
			'username': username,
			}).encode(), self.host)

		sleep(0.5)
		# insert the list
		if self.res_of_find_friends != [] and self.res_of_find_friends != None:
			self.find_user_box.insert('','end',values=self.res_of_find_friends)


	def find_by_nickname(self, nickname, var_friend_username):
		# clear username
		var_friend_username.set("")
		# clear the list
		items = self.find_user_box.get_children()
		for item in items:
			self.find_user_box.delete(item)
		# clear self.res_of_find_friends
		self.res_of_find_friends.clear()

		# sent request to server for looking user by nickname
		self.socket.sendto(json.dumps({
			'action': 'find_friends',
			'type': 'by_nickname',
			'nickname': nickname,
			}).encode(), self.host)

		sleep(0.5)

		# insert the list
		for item in self.res_of_find_friends:
			self.find_user_box.insert('','end',values=item)


	def click_friendlist(self, event):
		'''when find a friend and click item'''
		for item in self.find_user_box.selection():
			item_text = self.find_user_box.item(item,'values')
			self.selected_furture_friend = item_text


	def click_makesure_add(self):
		if self.selected_furture_friend != None:
			# If it's already a friend, then show warning and return
			for i in self.friends:	
				if self.selected_furture_friend[0] == i[0]:
					showwarning('warning', 'you and %s has been friend yet' % self.selected_furture_friend[0])
					return
			# can not be good friends with yourself 
			if self.selected_furture_friend[0] == self.username:
				showwarning('warning', 'can not be good friends with yourself')
				return

			self.socket.sendto(json.dumps({
				'action': 'add_friend',
				'username': self.username,
				'friendname': self.selected_furture_friend[0],
				'request_time': time(),
				}).encode(), self.host)
			# make a sleep to make user sure that the action is execute
			sleep(0.5)


	def gui_modify_info(self):
		if not self.is_login:
			return
		self.x = tk.Tk()
		self.x.title('SJChat')
		self.x.geometry('400x340')
		self.x.resizable(width=False, height=False)

		label_nickname = tk.Label(self.x, text='昵称:', width=120, font=('宋体',16,'normal'))
		label_nickname.place(x=33, y=35, width=120, height=30)
		self.var_nickname = tk.StringVar(self.x ,value=self.profile['nickname'])
		nickname = tk.Entry(self.x, textvariable=self.var_nickname, font=('宋体',16,'normal'))
		nickname.place(x=123, y=40, width=240, height=30)

		label_info = tk.Label(self.x, text='个性签名:',width=120, font=('宋体',16,'normal')) 
		label_info.place(x=13, y=85, width=120, height=30)
		self.info = tk.Text(self.x, width=22, height=6, font=('宋体',16,'normal'))
		self.info.insert(tk.INSERT, self.profile['userinfo'])
		self.info.place(x=123, y=90)

		label_info = tk.Label(self.x, text='性别:',width=120, font=('宋体',16,'normal')) 
		label_info.place(x=33, y=240, width=120, height=30)
		self.sex = IntVar()
		self.sex.set(0 if self.profile['sex'] == '男' else 1)
		rbtn_sex1 = tk.Radiobutton(self.x, text='男', variable=self.sex, value=0)
		rbtn_sex1.place(x=123, y=245)
		rbtn_sex2 = tk.Radiobutton(self.x, text='女', variable=self.sex, value=1)
		rbtn_sex2.place(x=220, y=245)

		btn_modify = tk.Button(self.x, text='确认修改', 
			command=self.modify_info, font=('宋体', 16, 'normal'))
		btn_modify.place(x=160, y=280)


	def modify_info(self):
		if self.var_nickname.get() == '' or self.var_nickname.get() == None:
			showwarning('Warning', 'nickname must be not None')
			return None
		
		self.socket.sendto(json.dumps({
			'action': 'update_profile',
			'username': self.username,
			'nickname': self.var_nickname.get(),
			'info': self.info.get(0.0, tk.END),
			'sex': self.sex.get(),
			}).encode(), self.host)

		self.x.destroy()


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
				elif js['action'] == 'login_inform':
					for i in self.friends:
						if i[0] == js['username']:
							i[3] = "在线"
							items = self.box.get_children()
							# remove pre item
							for item in items:
								if self.box.item(item,"values")[0] == js['username']:
									self.box.delete(item)
							# insert new item
							self.box.insert('',0,values=i)
							break
				elif js['action'] == 'logout_inform':
					for i in self.friends:
						if i[0] == js['username']:
							i[3] = "离线"
							items = self.box.get_children()
							# remove pre item
							for item in items:
								if self.box.item(item,"values")[0] == js['username']:
									self.box.delete(item)
							# insert new item
							self.box.insert('','end',values=i)
							break
				elif js['action'] == 'add_friend_request':
					self.sys_messages_count += 1
					self.var_sys_messages.set('系统消息（%d）' % self.sys_messages_count)
					t = []
					t.append("添加好友")
					t.append("%s 请求添加您为好友" % js['friendname'])
					t.append(ctime(int(float(js['request_time']))))
					self.system_message.append(t)
				elif js['action'] == 'update_friends':
					# clear items in self.box
					items = self.box.get_children()
					for item in items:
						self.box.delete(item)
					# update self.friends
					self.friends = js['friends']
					# insert item
					for i in self.friends:
						self.box.insert('','end',values=i)


				# elif js['action'] == 'sendmessage':
				# 	print('%s: %s' % (js['sender'], js['message']))
				elif js['action'] == 'update_profile_ok':
					self.profile = js['profile']
					self.top.title("SJChat %s" % self.profile['nickname'])
				elif js['action'] == 'res_of_find_friends':
					self.res_of_find_friends = js['friends']


	def logout(self):
		if not self.is_login:
			return
		self.socket.sendto(json.dumps({
				'action': 'exit',
				'username': self.username,
				}).encode(), self.host)
		self.top.destroy()


	def gui_sys_message(self):
		x = tk.Tk()
		x.title('system message')
		x.geometry('450x285')
		x.resizable(width=False, height=False)

		label_invisible0 = tk.Label(x, text='')
		label_invisible0.pack()
		# message list
		scrollbar = tk.Scrollbar(x)
		scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
		title = ['0','1','2']
		self.sys_message_box = ttk.Treeview(x, columns=title,
			yscrollcommand=scrollbar.set, height='10',
			show='headings')

		self.sys_message_box.column('0', width=60, anchor='w')
		self.sys_message_box.column('1', width=220, anchor='w')
		self.sys_message_box.column('2', width=150, anchor='w')

		self.sys_message_box.heading('0', text='类别')
		self.sys_message_box.heading('1', text='内容')
		self.sys_message_box.heading('2', text='时间')

		for i in self.system_message:
			self.sys_message_box.insert('','end',values=i)

		scrollbar.config(command=self.sys_message_box.yview)
		self.sys_message_box.pack()

		x.bind('<ButtonRelease-1>', self.click_messagelist)


	def click_messagelist(self, event):
		for item in self.sys_message_box.selection():
			username = re.match(r'(.*) 请求.*' ,self.sys_message_box.item(item,'values')[1]).group(1)
			if askokcancel('提示', '是否同意添加%s为好友？' % username):
				self.socket.sendto(json.dumps({
					'action': 'add_friend_ok',
					'username': self.username,
					'friendname': username,
					}).encode(), self.host)
			self.sys_message_box.delete(item)
			self.sys_messages_count -= 1
			if self.sys_messages_count < 0:
				self.sys_messages_count = 0
			self.var_sys_messages.set('系统消息（%d）' % self.sys_messages_count)


	def click_userlist(self, event):
		for item in self.box.selection():
			userprofile = self.box.item(item, 'values')
			self.gui_chat(userprofile)

	def gui_chat(self,userprofile):
		chat = tk.Tk()
		chat.title(userprofile[0] + "  签名：" + userprofile[2])
		chat.geometry('600x400')
		chat.resizable(width=False, height=False)

		scrollbar = tk.Scrollbar(chat)
		scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

		text = tk.Text(chat, width=50, height=15, font=('宋体',16,'normal'))
		# text.insert(tk.INSERT, "")
		text.config(state="disabled")
		text.pack()

		scrollbar.config(command=text.yview)

		var_input = StringVar(chat, '')
		entry_input = tk.Entry(chat, textvariable=var_input, font=('宋体',16,'normal'))
		entry_input.place(x=10, y=340, width=450, height=40)

		btn_send = tk.Button(chat, text='发送', width=10, height=2, command=lambda: self.send_message(var_input))
		btn_send.place(x=470, y=340)


	def send_message(self, message):
		print(message.get(),type(message.get()))
		showinfo('test', message.get())

	def gui_main(self):
		self.top = tk.Tk()
		self.top.title("SJChat %s" % self.profile['nickname'])
		self.top.geometry('360x600')
		self.top.resizable(width=False, height=False)
		
		label_invisible0 = tk.Label(self.top, text='')
		label_invisible0.pack()
		# friend list
		self.scrollbar = tk.Scrollbar(self.top)
		self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
		title = ['0','1','2','3']
		self.box = ttk.Treeview(self.top, columns=title,
			yscrollcommand=self.scrollbar.set, height='20',
			show='headings')

		self.box.column('0', width=60, anchor='w')
		self.box.column('1', width=60, anchor='w')
		self.box.column('2', width=150, anchor='w')
		self.box.column('3', width=35, anchor='w')

		self.box.heading('0', text='账号')
		self.box.heading('1', text='昵称')
		self.box.heading('2', text='简介')
		self.box.heading('3', text='状态')

		for i in self.friends:
			self.box.insert('','end',values=i)

		self.scrollbar.config(command=self.box.yview)
		self.box.pack()

		# action menu
		self.addfriend = tk.Button(self.top, text='添加好友', command=self.gui_add_friend, font=('宋体',14,'normal'))
		self.addfriend.place(x=60, y=480, width=90)

		self.btn_modify_info = tk.Button(self.top, text='修改信息', command=self.gui_modify_info, font=('宋体',14,'normal'))
		self.btn_modify_info.place(x=180, y=480, width=90)

		self.var_sys_messages = StringVar()
		self.var_sys_messages.set('系统消息（%d）' % self.sys_messages_count)

		self.btn_modify_info = tk.Button(self.top, textvariable=self.var_sys_messages, command=self.gui_sys_message, font=('宋体',14,'normal'))
		self.btn_modify_info.place(x=100, y=530, width=150)

		self.top.protocol("WM_DELETE_WINDOW", self.logout)

		self.box.bind('<ButtonRelease-1>', self.click_userlist)

		tk.mainloop()


t = SJChat(('127.0.0.1', 12346))
