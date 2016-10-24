# -*- coding: utf-8 -*-

import json
import time
from wechat.wrapper import WeChatHandler
from wechat.models import User, Activity, Ticket


class ErrorHandler(WeChatHandler):

    def check(self):
        return True

    def handle(self):
        return self.reply_text('对不起，服务器现在有点忙，暂时不能给您答复 T T')


class DefaultHandler(WeChatHandler):
    # 用于进行对输入的默认消息进行检验
    # 如果是可以计算的表达式，返回计算结果
    def check(self):   
        arith_chars = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '+', '-', '*', '/', '(', ')']
        input_text = self.input['Content']
        for char in input_text:
            if char in arith_chars:
                continue
            else:
                return False
        return True

    def handle(self):
        if self.check():
            try:
                return self.reply_text(str(eval(self.input['Content'])))
            except:
                return self.reply_text('您输入的表达式有误')
        else:
            return self.reply_text('您输入的不是一个表达式')


class HelpOrSubscribeHandler(WeChatHandler):

    def check(self):
        return self.is_text('帮助', 'help') or self.is_event('scan', 'subscribe') or \
               self.is_event_click(self.view.event_keys['help'])

    def handle(self):
        return self.reply_single_news({
            'Title': self.get_message('help_title'),
            'Description': self.get_message('help_description'),
            'Url': self.url_help(),
        })

class UnbindOrUnsubscribeHandler(WeChatHandler):

    def check(self):
        return self.is_text('解绑') or self.is_event('unsubscribe')

    def handle(self):
        self.user.student_id = ''
        self.user.save()
        return self.reply_text(self.get_message('unbind_account'))


class BindAccountHandler(WeChatHandler):

    def check(self):
        return self.is_text('绑定') or self.is_event_click(self.view.event_keys['account_bind'])

    def handle(self):
        return self.reply_text(self.get_message('bind_account'))


class BookEmptyHandler(WeChatHandler):

    def check(self):
        return self.is_event_click(self.view.event_keys['book_empty'])

    def handle(self):
        return self.reply_text(self.get_message('book_empty'))

# finished
# show available tickets
class BookWhatHandler(WeChatHandler):

    def check(self):
        return self.is_text('抢啥', 'activity') or self.is_event_click(self.view.event_keys['book_what']) 

    def handle(self):
        currentTime = time.time()
        avail_activities = []
        return_news = []
        all_activities = Activity.objects.all()
        for act in all_activities:
            if currentTime <= time.mktime(act.book_start.timetuple()) and act.status == 1:
                avail_activities.append(act)
                one_news = {
                    'Title': act.name,
                    'Description': act.description,
                    'Url': self.book_what(act.id)
                }
                return_news.append(one_news)
        return self.reply_news(return_news)

# finished
# show owned tickets
class GetTicketHandler(WeChatHandler):

    def check(self):
        return self.is_text("查票", 'check tickets') or self.is_event_click(self.view.event_keys['get_ticket'])

    def handle(self):
        this_user = User.objects.get(open_id=self.user.open_id)
        all_tickets = Ticket.objects.filter(student_id=this_user.student_id)
        if len(all_tickets) == 0:
            return self.reply_text("还没有您的订票。输入 订票+活动名称 进行订票")
        return_news = []
        for ticket in all_tickets:
            one_news = {
                'Title': ticket.activity.name,
                'Description': ticket.activity.description,
                'Url': self.get_ticket(ticket.unique_id)
            }
            return_news.append(one_news)
        return self.reply_news(return_news)

# finished
# book by click the button
class ClickBookTicketHandler(WeChatHandler):

    def check(self):
        try:
           return self.input['EventKey'].startswith("BOOKING_ACTIVITY")
        except:
            return False 

    def handle(self):
        currentTime = time.time()
        currentUser = User.objects.get(open_id=self.user.open_id)
        act_id = int(self.input['EventKey'].split("_")[-1])
        act = Activity.objects.get(pk=act_id)

        if act.remain_tickets == 0:
            return self.reply_text(act.name + "活动已经没有剩余票了QAQ")

        if currentTime <= time.mktime(act.book_start.timetuple()):
            return self.reply_text(act.name + "活动还没开始订票呢QAQ")

        if currentTime >= time.mktime(act.book_end.timetuple()):
            return self.reply_text(act.name + "活动已经结束订票了QAQ")

        try:
            Ticket.objects.get(student_id=currentUser.student_id, activity=act)
            return self.reply_text("您已经订了"+act.name+"的票， 请不要重复订票！")
        except:
            unique_id = self.input['EventKey'][-1] + " " + currentUser.open_id + " " + str(currentTime)
            ticket = Ticket(student_id=currentUser.student_id, unique_id=unique_id, activity=act, status=1)
            ticket.save()
            act.remain_tickets -= 1
            act.save()
            return self.reply_text("您已经订了"+act.name+"的票， 请到时参加！")

# finished
# book by send text msg
class TextBookTicketHandler(WeChatHandler):

    def check(self):
        try:
            return self.input['Content'].startswith("抢票") or self.input['Content'].startswith("get ticket")
        except:
            return False

    def handle(self):
        split_words = self.input['Content'].split(" ")
        word_num = len(split_words)
        act_name = ""
        for i in range(1, word_num):
            act_name += split_words[i] + " "
        act_name = act_name.strip()

        try:
            act = Activity.objects.get(name=act_name)
        except:
            return self.reply_text("活动不存在，请重新输入")

        currentTime = time.time()
        currentUser = User.objects.get(open_id=self.user.open_id)

        if act.remain_tickets == 0:
            return self.reply_text(act.name + "活动已经没有剩余票了QAQ")

        if currentTime <= time.mktime(act.book_start.timetuple()):
            return self.reply_text(act.name + "活动还没开始订票呢QAQ")

        if currentTime >= time.mktime(act.book_end.timetuple()):
            return self.reply_text(act.name + "活动已经结束订票了QAQ")

        try:
            Ticket.objects.get(student_id=currentUser.student_id, activity=act)
            return self.reply_text("您已经订了"+act.name+"的票， 请不要重复订票！")
        except:
            unique_id = self.input['EventKey'][-1] + " " + currentUser.open_id + " " + str(currentTime)
            ticket = Ticket(student_id=currentUser.student_id, unique_id=unique_id, activity=act, status=1)
            ticket.save()
            act.remain_tickets -= 1
            act.save()
            return self.reply_text("您已经订了"+act.name+"的票， 请到时参加！")

# 
# 
class RefundTicketHandler(WeChatHandler):

    def check(self):
        try:
            return self.input['Content'].startswith('退票') or self.input['Content'].startswith("refund")
        except:
            return False

    def handle(self):
        split_words = self.input['Content'].split(" ")
        word_num = len(split_words)
        act_name = ""
        for i in range(1, word_num):
            act_name += split_words[i] + " "
        act_name = act_name.strip()

        try:
            act = Activity.objects.get(name=act_name)
        except:
            return self.reply_text("活动不存在，请重新输入")

        currentTime = time.time()
        currentUser = User.objects.get(open_id=self.user.open_id)

        try:
            ticket = Ticket.objects.get(student_id=currentUser.student_id, activity=act)
        except:
            return self.reply_text("您没有"+act_name+"活动的票QAQ")

        if currentTime >= time.mktime(ticket.activity.book_end.timetuple()):
            return self.reply_text(act_name + "的订票已经结束，您不能退票了TAT")

        act.remain_tickets += 1
        act.save()
        ticket.delete()
        return self.reply_text("您已经退了"+act_name+"的票~")