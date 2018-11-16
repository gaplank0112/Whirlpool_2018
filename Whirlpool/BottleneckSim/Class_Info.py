__version__ = '1.0'
__author__ = 'Greg Plank'

'''
This class contains the open and close hours by day of the week as input by the Business Hours table.
The entire class object is added as a custom attribute on the object utilizing the hours.
'''

import sim_server
import datetime
import utilities

low, med, high = 2, 5, 9
debug_obj = sim_server.Debug()
model_obj = sim_server.Model()

class BusinessHours(object):
    def __init__(self, name):
        self.name = name
        self.operating_hours = {}
        self.utc_offset = 0
        self.observe_daylight_savings = False

    def __iter__(self):
        for attr, value in self.__dict__.iteritems():
            yield attr, value

    def convert_utc_to_local(self, utc_time):
        offset = self.utc_offset
        local_time = utc_time + datetime.timedelta(hours=offset)
        if self.observe_daylight_savings == True: # does this location do daylight savings?
            debug_obj.trace(high, str(utilities.check_daylight_savings(local_time)))
            if utilities.check_daylight_savings(local_time):
                local_time = local_time + datetime.timedelta(hours=1)
        debug_obj.trace(high, "  Converting UTC to local time")
        debug_obj.trace(high, "  UTC time %s %s " % (utc_time.strftime("%a"), str(utc_time)))
        debug_obj.trace(high, "  Local time %s %s " % (local_time.strftime("%a"), str(local_time)))
        return local_time

    def convert_local_to_utc(self, local_time):
        offset = self.utc_offset
        utc_time = local_time - datetime.timedelta(hours=offset)
        if self.observe_daylight_savings == True:  # does this location do daylight savings?
            debug_obj.trace(high, str(utilities.check_daylight_savings(local_time)))
            if utilities.check_daylight_savings(local_time):  # is daylight savings in effect?
                utc_time = utc_time - datetime.timedelta(hours=1)
        debug_obj.trace(high, "  Converting local time to UTC")
        debug_obj.trace(high, "  Local time " + str(local_time))
        debug_obj.trace(high, "  UTC time "+ str(utc_time))
        return utc_time

    def get_action(self, idx):
        if idx % 2 == 0:  # even number
            return 'OPEN'
        return 'CLOSE'

    def is_object_open(self, bh_type, check_datetime):
        local_datetime = self.convert_utc_to_local(check_datetime)
        is_open = True
        day_of_week = int(local_datetime.strftime("%w"))
        try:
            hours_list = self.operating_hours[bh_type]
        except:
            return is_open
        debug_obj.trace(med, "\n Checking UTC %s, %s Local %s %s, %s" % (check_datetime.strftime("%a"), check_datetime,
                                                                         local_datetime.strftime("%a"), local_datetime,
                                                                         self.name))
        debug_obj.trace(med, "   %s hours %s" % (bh_type, hours_list))
        start_idx = day_of_week * 2  # closing time on any given weekday
        offset = -14

        for idx in range(start_idx,start_idx + 16) :
            find_hour = hours_list[idx % len(hours_list)]
            debug_obj.trace(high, "\t\t Loop count: %s, index: %s, hour = %s" % (idx, idx, find_hour))
            if find_hour != "":
                action_type = self.get_action(idx)
                date_offset = offset // 2
                debug_obj.trace(high, "\t\t datetime offset %s" % date_offset)
                action_hour = datetime.time(int(find_hour[:2]), int(find_hour[-2:]))
                debug_obj.trace(high, "\t\t action hour %s " % action_hour)
                action_date = local_datetime.date() + datetime.timedelta(date_offset)
                debug_obj.trace(high, "\t\t action date %s" % action_date)
                action_datetime = datetime.datetime.combine(action_date, action_hour)
                debug_obj.trace(high, "    Date offset %s, %s datetime %s %s" % (offset, action_type,
                                                                                 action_datetime.strftime("%a"),
                                                                                 action_datetime))
                if action_type == "OPEN" and local_datetime >= action_datetime:
                    is_open = True
                if action_type == "CLOSE" and local_datetime > action_datetime:
                    is_open = False
            debug_obj.trace(high, "    End of is-open loop step. Currently %s" % is_open)
            offset += 1
        return is_open

    def next_opening_datetime(self, bh_type, check_datetime):
        debug_obj.trace(low,'    Checking next opening')
        action_datetime = check_datetime
        local_datetime = self.convert_utc_to_local(check_datetime)
        day_of_week = int(local_datetime.strftime("%w"))
        try:
            hours_list = self.operating_hours[bh_type]
            debug_obj.trace(med, '    Hours list = %s' % hours_list)
        except:
            debug_obj.trace(med, '    No hours list found for type %s at location %s'
                            % (bh_type, self.name))
            return action_datetime

        start_idx = day_of_week * 2
        offset = 0
        debug_obj.trace(high,'DELETE %s, %s, %s, %s, %s' % (start_idx, offset, hours_list,bh_type, check_datetime))
        for idx in range(start_idx, start_idx + 16, 2):
            find_hour = hours_list[idx % len(hours_list)]
            debug_obj.trace(high, "\t\t Loop count: %s, index: %s, hour = %s" % (idx, idx, find_hour))
            if find_hour != "":
                date_offset = offset // 2
                debug_obj.trace(high, "\t\t datetime offset %s" % date_offset)
                action_hour = datetime.time(int(find_hour[:2]), int(find_hour[-2:]))
                debug_obj.trace(high, "\t\t action hour %s " % action_hour)
                action_date = local_datetime.date() + datetime.timedelta(date_offset)
                debug_obj.trace(high, "\t\t action date %s" % action_date)
                action_datetime = datetime.datetime.combine(action_date, action_hour)
                debug_obj.trace(high, "    Date offset %s, datetime %s %s"
                                % (offset, action_datetime.strftime("%a"), action_datetime))
                if action_datetime < model_obj.starttime or action_datetime < local_datetime:
                    continue
                else:
                    break
            offset += 2

        return self.convert_local_to_utc(action_datetime)






