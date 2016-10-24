import time
import os
from WeChatTicket import settings

from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout

from codex.baseerror import *
from codex.baseview import APIView
from wechat.models import User, Activity, Ticket
from wechat.views import CustomWeChatView

# finished
class AdminLogin(APIView):

	def get(self):
		if self.request.user.is_authenticated():
			return 0
		else:
			raise ValidateError("User not log in")

	def post(self):
		self.check_input('username', 'password')
		user = authenticate(username=self.input['username'],password=self.input['password'])
		if user is not None:
			if user.is_active:
				if user.is_superuser:
					login(self.request, user)
				else:
					raise ValidateError("Non superuser log in")
			else:
				raise ValidateError("User not active")
		else:
			raise ValidateError("User does not exist")

# finished
class AdminLogout(APIView):

	def post(self):
		try:
			logout(self.request)
		except:
			raise ValidateError("Logout failed")

# finished
class ActivityDetail(APIView):

	def get(self):
		if self.request.user.is_authenticated():
			self.check_input('id')
			db_data = Activity.objects.get(pk=self.input['id'])
			front_data = {
				'id': db_data.id,
				'name': db_data.name,
				'key': db_data.key,
				'startTime': time.mktime(db_data.start_time.timetuple()),
				'endTime': time.mktime(db_data.end_time.timetuple()),
				'place': db_data.place,
				'bookStart': time.mktime(db_data.book_start.timetuple()),
				'bookEnd': time.mktime(db_data.book_end.timetuple()),
				'totalTickets': db_data.total_tickets,
				'picUrl': db_data.pic_url,
				'bookedTickets': db_data.total_tickets - db_data.remain_tickets,
				'usedTickets': db_data.total_tickets,
				'currentTime': time.time(),
				'status': db_data.status
			}
			return front_data
		else:
			raise ValidateError('Need user log in')

	def post(self):
		currentTime = time.time()
		if self.request.user.is_authenticated():
			# self.check_input('id','name','place','description','picUrl','startTime','endTime','bookStart','bookEnd','totalTickets','status')
			to_change = Activity.objects.get(id=self.input['id'])
			to_change.description = self.input['description']
			to_change.picUrl = self.input['picUrl']

			# do this for some bug
			startTime = to_change.start_time
			endTime = to_change.end_time
			bookStart = to_change.book_start

			if currentTime <= time.mktime(endTime.timetuple()):
				to_change.start_time = self.input['startTime']
				to_change.end_time = self.input['endTime']

			if to_change.status == 0:
				to_change.book_start = self.input['bookStart']
				to_change.status = self.input['status']

			if currentTime <= time.mktime(startTime.timetuple()):
				to_change.book_end = self.input['bookEnd']

			if currentTime <= time.mktime(bookStart.timetuple()):
				to_change.total_tickets = self.input['totalTickets']

			to_change.save()
		else:
			raise ValidateError("Need user log in")

# finished
class ActivityList(APIView):

	def get(self):
		if self.request.user.is_authenticated():
			origin_list = Activity.objects.filter(status=1)
			return_list = []
			for i in origin_list:
				new_item = {'id': i.id}
				new_item['name'] =  i.name
				new_item['description'] = i.description
				new_item['startTime'] = time.mktime(i.start_time.timetuple())
				new_item['endTime'] = time.mktime(i.end_time.timetuple())
				new_item['place'] = i.place
				new_item['bookStart'] = time.mktime(i.book_start.timetuple())
				new_item['bookEnd'] = time.mktime(i.book_end.timetuple())
				new_item['currentTime'] = time.time()
				new_item['status'] = i.status
				return_list.append(new_item)
			return return_list
		else:
			raise ValidateError("User not log in")

# finished
class ActivityDelete(APIView):

	def post(self):
		self.check_input('id')
		try:
			Activity.objects.get(pk=self.input['id']).delete()
		except:
			raise LogicError('Delete activity failed')

# finished
class ActivityCreate(APIView):
	def post(self):
		if self.request.user.is_authenticated():
			try:
				new_acitivity = Activity(
					name=self.input['name'],
					key=self.input['key'],
					description=self.input['description'],
					start_time=self.input['startTime'],
					end_time=self.input['endTime'],
					place=self.input['place'],
					book_start=self.input['bookStart'],
					book_end=self.input['bookEnd'],
					total_tickets=self.input['totalTickets'],
					status=self.input['status'],
					pic_url=self.input['picUrl'],
					remain_tickets=self.input['totalTickets']
				)
				new_acitivity.save()
				return new_acitivity.id
			except:
				raise LogicError('Error creating new activity')
		else:
			raise ValidateError('Need user log in')

# finished
class ActivityMenu(APIView):

	def get(self):
		if self.request.user.is_authenticated():
			menuIndex = 0
			currentTime = time.time()
			all_activities = Activity.objects.all()
			avail_activities = []
			for act in all_activities:
				if currentTime < time.mktime(act.book_start.timetuple()) and act.status:
					avail = {
						'id': act.id,
						'name': act.name,
						'menuIndex': menuIndex
					}
					avail_activities.append(avail)
			return avail_activities
		else:
			raise ValidateError("Need user log in")

	def post(self):
		if self.request.user.is_authenticated():
			all_tickets = []
			for id in self.input:
				object = Activity.objects.get(pk=id)
				all_tickets.append(object)
			CustomWeChatView.update_menu(all_tickets)
		else:
			raise ValidateError("Need user log in")

# finished
class ActivityCheckin(APIView):

	def post(self):
		self.check_input('actId', 'studentId')
		act = Activity.objects.get(id=self.input['actId'])
		try:
			ticket = Ticket.objects.get(student_id=self.input['studentId'], activity=act)
			ticket.status = 2
			ticket.save()
			return {
				'ticket': self.input['ticket'],
				'studentId': self.input['studentId']
			}
		except:
			raise LogicError("User didn't buy this ticket")

# finished
class ImageUpload(APIView):

	def post(self):
		if self.request.user.is_authenticated():
			self.check_input('image')
			image = self.input['image'][0]
			with open(os.path.join(settings.STATIC_ROOT, image.name), 'wb+') as new_img:
				for chunk in image.chunks():
					new_img.write(chunk)
				#new_img.close()
			return settings.SITE_DOMAIN + '/' + image.name
		else:
			raise ValidateError('User not log in')