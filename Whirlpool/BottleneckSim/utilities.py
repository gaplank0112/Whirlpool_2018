# Regular utilities used in various places of the project

import sys
sys.path.append("C:\Python26\SCG_64\Lib")
import sim_server
import datetime

low, med, high = 2, 5, 8
debug_obj = sim_server.Debug()
model_obj = sim_server.Model()


def get_timezone_offset(tz_str):
    tz_info = timezone_dict[tz_str]
    debug_obj.trace(med,"  tz_info = %s %s" % (tz_str, tz_info))
    return tz_info[0], tz_info[1]

def get_object(object_name):
    try:
        return sim_server.Site(object_name)
    except:
        pass

    try:
        return sim_server.Customer(object_name)
    except:
        pass

    try:
        return sim_server.WorkCenter(object_name)
    except:
        pass

    try:
        return sim_server.WorkResource(object_name)
    except:
        pass

def str_datetime(py_datetime):
    return datetime.datetime.strftime(py_datetime, '%m/%d/%Y %H:%M:%S')

def check_daylight_savings(input_datetime): #TODO: create better lookups for location based DST and flexible start/ends
    input_year = input_datetime.year
    dst_start = datetime.datetime(input_year, 3, 14, 2, 0)
    dst_end = datetime.datetime(input_year, 11, 14, 2, 0)
    return dst_start <= input_datetime < dst_end

def profile_stats(script_name, start_time, stop_time):
    process_time = stop_time - start_time
    profile_dict = model_obj.getcustomattribute('ScriptProfiles')
    if script_name not in profile_dict:
        profile_dict[script_name] = {'time':process_time, 'count':1}
    else:
        debug_obj.trace(low,'DELETE going into profiler %s, %s, %s, %s'
                        % (script_name, start_time, stop_time, process_time))
        profile_dict[script_name]['time'] += process_time
        profile_dict[script_name]['count'] += 1


timezone_dict = {
    "Dateline Standard Time":(-12,False),
"FLE Standard Time":(2,False),
"Israel Standard Time":(2,False),
"Samoa Standard Time":(-11,False),
"E. Europe Standard Time":(2,False),
"Hawaiian Standard Time":(-10,False),
"Arabic Standard Time":(3,False),
"Alaskan Standard Time":(-9,False),
"Arab Standard Time":(3,False),
"Pacific Standard Time (Mexico)":(-8,False),
"Russian Standard Time":(3,False),
"Pacific Standard Time":(-8,True),
"E. Africa Standard Time":(3,False),
"US Mountain Standard Time":(-7,False),
"Iran Standard Time":(3.5,False),
"Mountain Standard Time (Mexico)":(-7,False),
"Arabian Standard Time":(4,False),
"Mountain Standard Time":(-7,True),
"Azerbaijan Standard Time":(4,False),
"Central America Standard Time":(-6,False),
"Mauritius Standard Time":(4,False),
"Central Standard Time":(-6,True),
"Georgian Standard Time":(4,False),
"Central Standard Time (Mexico)":(-6,False),
"Caucasus Standard Time":(4,False),
"Canada Central Standard Time":(-6,False),
"Afghanistan Standard Time":(4,False),
"SA Pacific Standard Time":(-5,False),
"Ekaterinburg Standard Time":(5,False),
"Eastern Standard Time":(-5,True),
"Pakistan Standard Time":(5,False),
"US Eastern Standard Time":(-5,False),
"West Asia Standard Time":(5,False),
"Venezuela Standard Time":(-4,False),
"India Standard Time":(5.5,False),
"Paraguay Standard Time":(-4,True),
"Sri Lanka Standard Time":(6,False),
"Atlantic Standard Time":(-4,False),
"Nepal Standard Time":(5.75,False),
"Central Brazilian Standard Time":(-4,False),
"Central Asia Standard Time":(6,False),
"SA Western Standard Time":(-4,False),
"Bangladesh Standard Time":(6,False),
"Pacific SA Standard Time":(-4,False),
"N. Central Asia Standard Time":(6,False),
"Newfoundland Standard Time":(-3,False),
"Myanmar Standard Time":(6.5,False),
"E. South America Standard Time":(-3,False),
"S.E. Asia Standard Time":(7,False),
"Argentina Standard Time":(-3,False),
"North Asia Standard Time":(7,False),
"SA Eastern Standard Time":(-3,False),
"China Standard Time":(8,False),
"Greenland Standard Time":(-3,False),
"North Asia East Standard Time":(8,False),
"Montevideo Standard Time":(-3,False),
"Singapore Standard Time":(8,False),
"W. Australia Standard Time":(8,False),
"Mid-Atlantic Standard Time":(-2,False),
"Taipei Standard Time":(8,False),
"Azores Standard Time":(-1,False),
"Ulaanbaatar Standard Time":(8,False),
"Cape Verde Standard Time":(-1,False),
"Tokyo Standard Time":(9,False),
"Morocco Standard Time":(0,True),
"Korea Standard Time":(9,False),
"Yakutsk Standard Time":(9,False),
"GMT Standard Time":(0,False),
"Cen. Australia Standard Time":(9.5,False),
"Greenwich Standard Time":(0,False),
"AUS Central Standard Time":(9,False),
"W. Europe Standard Time":(1,False),
"E. Australia Standard Time":(10,False),
"Central Europe Standard Time":(1,False),
"AUS Eastern Standard Time":(10,False),
"Romance Standard Time":(1,False),
"West Pacific Standard Time":(10,False),
"Central European Standard Time":(1,False),
"Tasmania Standard Time":(10,False),
"W. Central Africa Standard Time":(1,False),
"Vladivostok Standard Time":(10,False),
"Namibia Standard Time":(2,False),
"Magadan Standard Time":(11,False),
"Jordan Standard Time":(2,True),
"Central Pacific Standard Time":(11,False),
"GTB Standard Time":(2,False),
"New Zealand Standard Time":(12,False),
"Middle East Standard Time":(3,False),
"Egypt Standard Time":(2,False),
"Fiji Standard Time":(12,False),
"Syria Standard Time":(2,True),
"Kamchatka Standard Time":(3,False),
"South Africa Standard Time":(2,False),
"Tonga Standard Time":(13,False),
"UTC-12:00":(-12,False),
"UTC-11:00":(-11,False),
"UTC-10:00":(-10,False),
"UTC-9:00":(-9,False),
"UTC-8:00":(-8,False),
"UTC-7:00":(-7,False),
"UTC-6:00":(-6,False),
"UTC-5:00":(-5,False),
"UTC-4:00":(-4,False),
"UTC-3:00":(-3,False),
"UTC-2:00":(-2,False),
"UTC-1:00":(-1,False),
"UTC":(0,False),
"UTC+1:00":(1,False),
"UTC+2:00":(2,False),
"UTC+3:00":(3,False),
"UTC+4:00":(4,False),
"UTC+4:30":(4.5,False),
"UTC+5:00":(5,False),
"UTC+5:30":(5.5,False),
"UTC+6:00":(6,False),
"UTC+7:00":(7,False),
"UTC+8:00":(8,False),
"UTC+9:00":(9,False),
"UTC+10:00":(10,False),
"UTC+11:00":(11,False),
"UTC+12:00":(12,False),
"UTC+13:00":(13,False)
}

def total_seconds(arg_timedelta):
    return arg_timedelta.days * 86400 + arg_timedelta.seconds


