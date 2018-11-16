import sys
import sim_server
import datetime
sys.path.append("C:\Python26\SCG_64\Lib")

low, med, high = 2, 5, 9
debug_obj = sim_server.Debug()
model_obj = sim_server.Model()

def main(consumer, site_obj, resources):
    sim_server.Debug().trace(2,'-'*30)
    sim_server.Debug().trace(2,'Work resource constraint check called at %s for %s'
                             % (sim_server.NowAsString(), site_obj.name))

    if consumer.custom2 == 'RELEASED':
        consumer.custom2 = '' # reset the released flag so other places do not release immediately
        debug_obj.trace(low, ' Consumer released to resources')

        return True
    else:
        sched_time = datetime.datetime.utcfromtimestamp(sim_server.Now()) + datetime.timedelta(minutes=1)
        for work_resource in resources:
            review_times = work_resource.getcustomattribute('ReviewTimes')
            if sched_time not in review_times:
                review_times.append(sched_time)
                sim_server.ScheduleCustomEvent('QueuePrioritization', '1 MIN', [work_resource])
                debug_obj.trace(med, ' QueuePrioritization scheduled for %s at %s' % (work_resource.name, sched_time))
            else:
                debug_obj.trace(med, ' QueuePrioritization already scheduled for %s at %s'
                                % (work_resource.name, sched_time))

        return False



