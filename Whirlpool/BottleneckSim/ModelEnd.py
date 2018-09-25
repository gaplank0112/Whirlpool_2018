import sys
sys.path.append("C:\Python26\SCG_64\Lib")
import sim_server

low, med, high = 2, 5, 9
debug_obj = sim_server.Debug()
model_obj = sim_server.Model()

def main():
    debug_obj.trace(low,'-'*30)
    debug_obj.trace(low,'End Model called at ' + sim_server.NowAsString())
    debug_obj.trace(low," ")
    profile_dict = model_obj.getcustomattribute('ScriptProfiles')
    for k, v in profile_dict.iteritems():
        debug_obj.trace(low, '%s, time, count %s' % (k, v))
        debug_obj.trace(low, '%s, time, count %s' % (k, v), 'script_profile.txt')