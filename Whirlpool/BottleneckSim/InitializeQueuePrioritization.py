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

low, med, high = 2, 5, 9
debug_obj = sim_server.Debug()
model_obj = sim_server.Model()


def main():
    debug_obj.trace(low, " Initialize Queue Prioritization called at " + sim_server.NowAsString())
    script_start = datetime.datetime.now()
    sim_server.AddPythonScript('QueuePrioritization', 'main')
    sim_server.AddPythonScript('WorkResourceConstraint', 'main')

    sites = sim_server.Model().sites
    lanes = sim_server.Model().lanes
    sched_time = datetime.datetime.utcfromtimestamp(sim_server.Now()) + datetime.timedelta(seconds=1)
    sched_time_str = utilities.str_datetime(sched_time)

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
        weighted_average_trans_time = 0.0
        for mode in lane.modes:
            mode.constraintcheckscript = 'WorkResourceConstraint'
            debug_obj.trace(high,' Set mode constraint check for lane %s mode %s'
                            % (lane.name, mode.name))
            # -- We calculate the average transit time by running the distribution 1000 times. This is needed for
            # -- our 'is the site open for delivery' calculations
            average_transit_time = get_avg_transit_time(mode)
            mode.setcustomattribute('AverageTransitTime', average_transit_time)
            debug_obj.trace(low, '   Average trans time %s, mode %s, mode parameter(weight) %s' %
                            ((float(average_transit_time)/86400.0), mode.name, mode.modeparameter))
            weighted_average_trans_time += average_transit_time * (mode.modeparameter / 100)
        lane.setcustomattribute('WgtAvgTransTime', weighted_average_trans_time)
        debug_obj.trace(low, '   Weighted Average trans time for lane %s = %s \n' %
                        (lane.name, float(weighted_average_trans_time) / 86400.0))

    set_outbound_queue_priority()

    # -- Collect usage stats of the scripts for profiling
    utilities.profile_stats('InitializeQueuePrioritization', script_start, datetime.datetime.now())


def get_avg_transit_time(mode_obj):
    transit_time = 0.0
    for i in range(1000):
        transit_time += float(mode_obj.transportationtime.valueinseconds)


    return transit_time / 1000.0

def set_outbound_queue_priority():
    # -- Sort the queue by the prioritization sequence # TODO: Allow input from a global variable
    outbound_priority_dict = {'RDC': [['HMDPT'], ['_LDC'],['_OTHER', 'LOWES', 'BESTB']],
                              'FDC': [['SEARS', 'LOWES', 'BESTB'], ['OTHER'], ['_RDC']]}
    model_obj.setcustomattribute('OutboundQueuePriority', outbound_priority_dict)
