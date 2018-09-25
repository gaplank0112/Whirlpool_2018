'''
This script sets a check of the consumer queue whenever a FDC or RDC opens for shipping or receiving.
Without this check, items might get stuck in a queue waiting for another item to arrive to initiate a review.
'''

import sys
import sim_server
from utilities import str_datetime
from datetime import timedelta
sys.path.append("C:\Python26\SCG_64\Lib")

low, med, high = 2, 2, 2
debug_obj = sim_server.Debug()
model_obj = sim_server.Model()

def main(check_time, work_resource):
    debug_obj.trace(low,'-'*30)
    debug_obj.trace(low,'Opening Hours Check called ' + sim_server.NowAsString())
    site_obj = work_resource.owner

    sim_server.ScheduleCustomEvent("QueuePrioritization", str_datetime(check_time), [work_resource])
    check_time = check_time + timedelta(seconds=1.0)

    bh = site_obj.getcustomattribute('BusinessHours')
    review_times = work_resource.getcustomattribute('ReviewTimes')
    next_shipping_open = bh.next_opening_datetime('SHIPPING',check_time)
    next_receiving_open = bh.next_opening_datetime('RECEIVING',check_time)
    next_open_review = min(next_shipping_open, next_receiving_open)

    debug_obj.trace(low, ' At site %s, resource name %s' % (site_obj.name, work_resource.name))
    debug_obj.trace(high, '  Next UTC shipping open %s, Next UTC receiving open %s'
                    % (next_shipping_open, next_receiving_open))

    if next_open_review not in review_times:
        review_times.append(next_open_review)
        sim_server.ScheduleCustomEvent('OpeningHoursCheck', str_datetime(next_open_review),
                                       [next_open_review, work_resource])
        debug_obj.trace(med, ' OpeningHoursCheck scheduled for %s at %s'
                        % (work_resource.name, next_open_review))
    else:
        debug_obj.trace(med, ' OpeningHoursCheck already scheduled for %s at %s'
                        % (work_resource.name, next_open_review))


#Keep for Steve... this causes the model to 'end' prematurely
# def main(check_time, work_resource):
#     debug_obj.trace(low,'-'*30)
#     debug_obj.trace(low,'Opening Hours Check called ' + sim_server.NowAsString())
#
#
#     sim_server.ScheduleCustomEvent("QueuePrioritization", str_datetime(check_time), [work_resource])
#     check_time = check_time + timedelta(seconds=1.0)
#
#     bh = work_resource.getcustomattribute('BusinessHours')
#     review_times = work_resource.getcustomattribute('ReviewTimes')
#     next_shipping_open = bh.next_opening_datetime('SHIPPING',check_time)
#     next_receiving_open = bh.next_opening_datetime('RECEIVING',check_time)
#     next_open_review = min(next_shipping_open, next_receiving_open)
#     debug_obj.trace(low, 'DELETE/HIGH  %s, %s' % (next_shipping_open, next_receiving_open))
#
#     if next_open_review not in review_times:
#         review_times.append(next_open_review)
#         sim_server.ScheduleCustomEvent('OpeningHoursCheck', str_datetime(next_open_review), [work_resource])
#         debug_obj.trace(med, ' OpeningHoursCheck scheduled for %s at %s'
#                         % (work_resource.name, next_open_review))
#     else:
#         debug_obj.trace(med, ' OpeningHoursCheck already scheduled for %s at %s'
#                         % (work_resource.name, next_open_review))