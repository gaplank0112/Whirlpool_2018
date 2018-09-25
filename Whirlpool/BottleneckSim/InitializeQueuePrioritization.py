__version__ = '1.0'
__author__ = 'Greg Plank'

'''
This module adds internal python scripts and sets the first queue review if a FDC/RDC is closed at model start
'''

import sys
import sim_server
import datetime
import utilities
sys.path.append("C:\Python26\SCG_64\Lib")

low, med, high = 2, 5, 8
debug_obj = sim_server.Debug()
model_obj = sim_server.Model()


def main():
    debug_obj.trace(low, " Initialize Queue Prioritization called at " + sim_server.NowAsString())
    script_start = datetime.datetime.now()
    sim_server.AddPythonScript('QueuePrioritization', 'main')
    sim_server.AddPythonScript('WorkResourceConstraint', 'main')
    debug_obj.trace(high, 'Added python script ')

    sites = sim_server.Model().sites
    lanes = sim_server.Model().lanes
    sched_time = datetime.datetime.utcfromtimestamp(sim_server.Now()) + datetime.timedelta(seconds=1)
    sched_time_str = utilities.str_datetime(sched_time)
    debug_obj.trace(low,'DELETE sched time %s, str %s' % (sched_time,sched_time_str))
    for site in sites:
        # For each site with a work resource, we need to set a queue review at the next opening hour.
        for work_resource in site.workresources:
            work_resource.queuereviewpolicy = 1
            work_resource.queuereviewscript = 'QueuePrioritization'
            work_resource.setcustomattribute('ReviewTimes', [])
            sim_server.ScheduleCustomEvent('OpeningHoursCheck', sched_time_str, (sched_time, work_resource))
            debug_obj.trace(high,' Set queue review at %s for resource %s to %s, %s'
                           % (site.name, work_resource.name, work_resource.queuereviewpolicy,
                              work_resource.queuereviewscript))
    for lane in lanes:
        for mode in lane.modes:
            mode.constraintcheckscript = 'WorkResourceConstraint'
            debug_obj.trace(high,' Set mode constraint check for lane %s mode %s'
                            % (lane.name, mode.name))

    utilities.profile_stats('InitializeQueuePrioritization', script_start, datetime.datetime.now())

