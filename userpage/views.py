import time

from codex.baseerror import *
from codex.baseview import APIView

from wechat.models import User, Activity, Ticket

# finished
class UserBind(APIView):

    def validate_user(self):
        url = 'https://id.tsinghua.edu.cn/security_check'
        student_id = self.input['student_id']
        password = self.input['password']
        check_params = {'username':student_id, 'password':password}
        r = requests.post(url, data=check_params)
        
        if r.status_code == 403:
            return
        else:
            raise ValidateError('invalid username or password')

    def get(self):
        self.check_input('openid')
        return User.get_by_openid(self.input['openid']).student_id

    def post(self):
        self.check_input('openid', 'student_id', 'password')
        user = User.get_by_openid(self.input['openid'])
        self.validate_user()
        user.student_id = self.input['student_id']
        user.save()

# finished
class ActivityDetail(APIView):

    def get(self):
        self.check_input('id')
        this_activity = Activity.objects.get(pk=self.input['id'])
        if this_activity.status == 1:
            return {
                'name': this_activity.name,
                'key': this_activity.key,
                'startTime': time.mktime(this_activity.start_time.timetuple()),
                'endTime': time.mktime(this_activity.end_time.timetuple()),
                'place': this_activity.place,
                'bookStart': time.mktime(this_activity.book_start.timetuple()),
                'bookEnd': time.mktime(this_activity.book_end.timetuple()),
                'totalTickets': this_activity.total_tickets,
                'picUrl': this_activity.pic_url,
                'remainTickets': this_activity.remain_tickets,
                'currentTime': time.time()
            }
        else:
            raise LogicError("Activity not released")

# finished
class TicketDetail(APIView):

    def get(self):
        self.check_input('openid', 'ticket')
        ticket = Ticket.objects.get(unique_id=self.input['ticket'])
        return {
            'activityName': ticket.activity.name,
            'place': ticket.activity.place,
            'activityKey': ticket.activity.key,
            'uniqueId': ticket.unique_id,
            'startTime': time.mktime(ticket.activity.start_time.timetuple()),
            'endTime': time.mktime(ticket.activity.end_time.timetuple()),
            'currentTime': time.time(),
            'status': ticket.status
        }

