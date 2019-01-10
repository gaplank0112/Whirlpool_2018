import sys
import sim_server
import datetime
import utilities
sys.path.append("C:\Python26\SCG_64\Lib")

low, med, high = 2, 5, 9
debug_obj = sim_server.Debug()
model_obj = sim_server.Model()


def main(work_resource):
    debug_obj.trace(low,'-'*30)
    debug_obj.trace(low,'Queue prioritization called at ' + sim_server.NowAsString())
    script_start = datetime.datetime.now()
    # -- Set up a temporary container to hold results of is_open queries to avoid looping multiple times
    is_open_dict = {}
    back_order_sort = []
    site_obj = work_resource.owner
    consumer_queue = work_resource.waitingconsumerqueue
    debug_obj.trace(low, ' At site %s, resource name %s' % (site_obj.name, work_resource.name))
    debug_obj.trace(low, '  Units - utilized %s, available %s, total %s'
                   % (work_resource.utilizedunits, work_resource.availableunits, work_resource.unitcount))
    debug_obj.trace(low, '  Queue size = %s' % len(consumer_queue))

    if work_resource.availableunits == 0:
        debug_obj.trace(low,'  No available resources. Skipping this prioritization')
        return

    if len(consumer_queue) > 0:
        is_open_receiving, is_open_shipping = check_for_open(is_open_dict, site_obj)
        if is_open_shipping == False and is_open_receiving == False:
            return # -- The site is closed so no reason to prioritize anything now.

        if is_open_receiving is True:
            # -- Create a sorted list of items on back order to prioritize inbound shipments waiting for unload
            back_order_sort = get_back_order_list(site_obj)
            debug_obj.trace(high, '  Sorted back orders %s' % back_order_sort)

        # -- Filter out any items that can not be released because of open windows
        filtered_queue = filter_consumer_queue(consumer_queue, is_open_receiving, is_open_shipping,
                                               is_open_dict, work_resource)
        filtered_queue = prioritize_queue(filtered_queue, back_order_sort)

        if len(filtered_queue) > 0:
            debug_obj.trace(low, '\n  Releasing items from the filtered/prioritized queue')
            resources_available = work_resource.availableunits
            while len(filtered_queue) > 0 and resources_available > 0:
                debug_obj.trace(high, '    Queue size: %s, Resources available: %s'
                                % (len(filtered_queue), resources_available))
                queue_pick = filtered_queue[0]
                queue_pick.custom2 = 'RELEASED'
                queue_pick.resumefromwait()
                filtered_queue.remove(queue_pick)
                resources_available -= 1
        else:
            debug_obj.trace(low, '\n  No items to release from the filtered/prioritized queue')

    # -- Collect usage stats of the scripts for profiling
    utilities.profile_stats('QueuePrioritization', script_start, datetime.datetime.now())


def check_for_open(is_open_dict, site_obj):
    # -- Check to see if we have already looked at the opening hours for this site and use them.
    # -- If not, check for open hours and then add them to the dictionary for later
    try:
        open_booleans = is_open_dict[site_obj.name]
        is_open_receiving, is_open_shipping = open_booleans[0], open_booleans[1]
    except:
        is_open_receiving, is_open_shipping = \
            open_hours(site_obj, datetime.datetime.utcfromtimestamp(sim_server.Now()))
        # -- Add the results of the is_open query to the dictionary
        is_open_dict[site_obj.name] = (is_open_receiving, is_open_receiving)
    debug_obj.trace(med, '   Site is open receiving = %s, is open shipping = %s \n'
                    % (is_open_receiving, is_open_shipping))
    return is_open_receiving, is_open_shipping


def get_back_order_list(site_obj):
    back_order_list = []
    for site_product in site_obj.products:
        if site_product.currentorderquantity > 0.0:
            back_order_list.append((site_product.product.name, site_product.currentorderquantity))
    back_order_sort = sorted(back_order_list, key=lambda a: a[1],
                             reverse=True)  # -- Sort by the second element in the tuple
    return back_order_sort


def open_hours(site_obj, time_check):
    # is the site open for receiving? If not, remove all inbound shipments
    try:
        bh = site_obj.getcustomattribute('BusinessHours')
    except:
        debug_obj.logerror('Python - Queue Prioritization: No business hours attribute found for site %s. Assume'
                           'it is open.' % site_obj.name)
        return True, True
    is_open_receiving = bh.is_object_open("RECEIVING", time_check)
    # is the site open for shipping?
    is_open_shipping = bh.is_object_open("SHIPPING", time_check)
    return is_open_receiving, is_open_shipping


def filter_consumer_queue(queue, open_receiving, open_shipping, is_open_dict, work_resource):
    debug_obj.trace(low,'  Filtering Queue')
    filter_queue = []

    # -- Go through each criteria and determine if the condition is True or False or None (does not apply)
    for consumer in queue:
        shipment_type = get_shipment_type(consumer)
        debug_obj.trace(med, '  Shipment type %s, origin %s, destination %s'
                        % (shipment_type, consumer.items[0].orderfromname, consumer.items[0].shiptoname))

        # -- If this item was previously reviewed at the same time stamp, nothing would have changed. Therefore,
        # -- just pass this through to the filtered queue
        previously_reviewed, filter_value, sort_priority = check_previous_review(consumer)

        if previously_reviewed is True:
            add_item = [filter_value]
        else:
            add_item = []
            # -- Is the consumer item a shipment?
            add_item.append(check_for_objecttype(consumer))
            # -- If the shipment is an inbound shipment, is the site open for receiving
            add_item.append(check_receiving_open(shipment_type, open_receiving))
             # -- If the shipment is an outbound shipment, is the site open for shipping
            add_item.append(check_open_outbound(shipment_type, open_shipping))
             # -- If the shipment is an outbound shipment, are we within a shipping window for the destination
            add_item.append(check_delivery_open(shipment_type, consumer, is_open_dict, work_resource))
            debug_obj.trace(high,'      Type=Shipment? %s | IB:source recv open? %s | OB:source ship open? %s | '
                                 'OB:open at delivery? %s' % (add_item[0], add_item[1], add_item[2], add_item[3]))
            add_item = [x for x in add_item if x is not None] # remove any None items from the True/False list
            consumer.custom2 = utilities.str_datetime(datetime.datetime.utcfromtimestamp(sim_server.Now())) + '|' +\
                               str(all(add_item)) + '|' + '0.0'

        if all(add_item): # -- If everything is True, add the item to the list of items that can be released
            filter_queue.append(consumer)
    debug_obj.trace(high,'  Filtered Queue: %s' % filter_queue)
    return filter_queue


def check_previous_review(consumer):
    # -- The custom2 field is separated into Last date reviewed | Filter value | Sort Priority
    review_data = consumer.custom2.split('|')
    debug_obj.trace(low,str(review_data))

    if review_data[0] == sim_server.NowAsString():  # -- We have already reviewed this once at this timestamp
        return True, review_data[1], review_data[2]
    else:
        return False, False, 0.0

def get_shipment_type(consumer):
    if consumer.custom1:  # we tag inbound shipments as they arrive. If the item isn't tagged, it must an outbound
        shipment_data = consumer.custom1
        shipment_type, date_in_queue = shipment_data.split('|')
    else:
        shipment_type = 'OB'
        consumer.custom1 = shipment_type + '|' + sim_server.NowAsString()
    return shipment_type


def check_for_objecttype(consumer):
    if consumer.objecttype == 'SHIPMENT':
        return True
    else:
        return False


def check_receiving_open(shipment_type, is_open_receiving):
    if shipment_type == 'IB':
        if is_open_receiving:
            return True
        else:
            return False


def check_open_outbound(shipment_type, is_open_shipping):
    if shipment_type == 'OB':
        if is_open_shipping:
            return True
        else:
            return


def check_delivery_open(shipment_type, consumer, is_open_dict, work_resource):
    # TODO: use the 'weighted averaage transportation time' instead of trans lead time.
    # TODO: Anything over 12 hours transportation time can be released at any time.
    if shipment_type == 'OB':
        site_obj = consumer.items[0].shipto
        try:
            open_booleans = is_open_dict[site_obj.name]
            is_open_receiving, is_open_shipping = open_booleans[0], open_booleans[1]
        except:
            # -- Calculate the expected delivery date as current time + transit time from Drop Processing Order table
            origin = consumer.items[0].orderfrom
            destination = consumer.items[0].shipto
            lane_obj = utilities.get_lane(origin,destination)
            transit_time_hours = float(lane_obj.getcustomattribute('WgtAvgTransTime')/ 86400.0)
            debug_obj.trace(med,'    Weighted avg transit time = %s' % transit_time_hours)
            expected_delivery = datetime.datetime.utcfromtimestamp(sim_server.Now()) + \
                                datetime.timedelta(hours=transit_time_hours)
            is_open_receiving, is_open_shipping = open_hours(site_obj, expected_delivery)
            if transit_time_hours > 12.0:
                is_open_receiving = True
            # -- Add the results of the is_open query to the dictionary
            is_open_dict[site_obj.name] = (is_open_receiving, is_open_shipping)

            if is_open_receiving is False: # -- We need to schedule a resource check when the receive window opens
                schedule_resource_check(site_obj, expected_delivery, work_resource)

        return is_open_receiving


def prioritize_queue(queue, back_order_list):
    debug_obj.trace(low,'  Prioritizing Queue')
    for consumer in queue:
        previously_reviewed, filter_value, sort_priority = check_previous_review(consumer)

        if previously_reviewed is True and sort_priority != '0.0':
            consumer.setcustomattribute('queue_priority',sort_priority)
        else:
            # -- Set the base priority based on the type of shipment
            if get_shipment_type(consumer) == 'OB':
                sort_priority = '1'
                second_priority = get_OB_secondary_priority(consumer)
                sort_priority += second_priority
            else:
                sort_priority = '2'
                second_priority = get_IB_secondary_priority(back_order_list, consumer)
                sort_priority += second_priority
            # -- Add the time in the queue
            seconds_in_queue = get_seconds_in_queue(consumer)
            sort_seconds = 99999999 - seconds_in_queue
            sort_priority += '.' + ('00000000' + str(sort_seconds))[-8:]

            consumer.setcustomattribute('queue_priority',sort_priority)
            # -- We record the sort priority so we can skip this review later if the the review is at the
            # -- same time stamp
            consumer.custom2 = consumer.custom2.replace('|0.0','|' + str(sort_priority))

    sorted_queue = sorted(queue, key=lambda x: x.getcustomattribute('queue_priority'))

    debug_obj.trace(low,'--------------- %s  ----------------' % sim_server.NowAsString(), 'priority.txt')
    for item in sorted_queue:
        debug_obj.trace(low, '    Sorted Queue item: %s, %s, %s, %s' % (item.getcustomattribute('queue_priority'),
                                                 item.id,
                                             item.items[0].orderfromname,
                                             item.items[0].finaldestinationname))
        debug_obj.trace(low, '%s, %s, %s, %s' % (item.getcustomattribute('queue_priority'),
                                                 item.id,
                                             item.items[0].orderfromname,
                                             item.items[0].finaldestinationname), 'priority.txt')

    return sorted_queue


def get_seconds_in_queue(consumer):
    '''
    When a shipment arrives, we put the date arrived in custom 1 field element 1
    When an order is dropped, we put the drop date in custom 1 field element 1
    Subtract now time from the time started in queue. Concatenate the results onto the sort priority
    after the decimal point. This ensures a sort for items in the queue the longest.
    '''
    consumer_data = consumer.custom1
    shipment_type, date_in_queue = consumer_data.split('|')
    date_in_queue_datetime = datetime.datetime.strptime(date_in_queue, '%m/%d/%Y %H:%M:%S')
    time_in_queue = datetime.datetime.utcfromtimestamp(sim_server.Now()) - date_in_queue_datetime
    seconds_in_queue = utilities.total_seconds(time_in_queue)
    debug_obj.trace(high, '     Time start in queue, Now, Total Seconds %s, %s, %s' %
                    (date_in_queue, sim_server.NowAsString(), seconds_in_queue))
    return seconds_in_queue


def get_IB_secondary_priority(back_order_list, consumer):
    # -- Set the secondary IB priority based on whether the item is on backorder
    # -- Evaluate each item on the shipment. If any one of them is on backorder, add the index priority
    # -- to the highest index
    second_priority = 9999
    for item in consumer.items:
        for detail in item.details:
            debug_obj.trace(low, '    Prioritizaion - Ship Type, ProductName, Back Order list '
                                 'IB, %s, %s' % (detail.productname, back_order_list))
            index_sort = [i for i, v in enumerate(back_order_list) if v[0] == detail.productname]
            '''
            Explained in words: For each i, v in a enumerated list of back_order_list (that makes i the
            element's position in the enumerated list and v the original tuple) check if the tuple's
            first element is the product name, if so, append the result of the code before 'for' to a
            newly created list, here: i.
            '''
            if len(index_sort) == 0:
                # -- Product not on back order
                continue
            elif index_sort[0] < second_priority:
                second_priority = index_sort[0]
        second_priority = ('0000' + str(second_priority))[-4:]
    return second_priority


def get_OB_secondary_priority(consumer):
    # -- Set the secondary OB priority based on the destination
    # -- Currently hard coded but ideally will accept input
    second_priority = '9999'
    item = consumer.items[0]
    source_type = item.orderfrom.custom1
    destination_name = item.shiptoname
    obqp = model_obj.getcustomattribute('OutboundQueuePriority')
    priority_list = obqp[source_type]
    debug_obj.trace(high, '    Prioritization - Ship Type, SourceType, Destination, Priority:'
                          ' OB, %s, %s, %s' % (source_type, destination_name, priority_list))
    for index, pri_list in enumerate(priority_list):
        for element in pri_list:
            if element in destination_name:
                second_priority = ('0000' + str(index))[-4:]
                break
    return second_priority


def schedule_resource_check(destination_obj, earliest_delivery, work_resource):
    # -- Look for the next open receiving time at the destination
    bh = destination_obj.getcustomattribute('BusinessHours')
    next_open_review = bh.next_opening_datetime('RECEIVING',earliest_delivery)
    debug_obj.trace(high,'  Earliest delivery (UTC) %s, Next opening (UTC) %s' %
                    (earliest_delivery, next_open_review))

    # -- Determine if this time is already scheduled for review for this work resource
    review_times = work_resource.getcustomattribute('ReviewTimes')
    if next_open_review not in review_times:
        review_times.append(next_open_review)
        sim_server.ScheduleCustomEvent('OpeningHoursCheck', utilities.str_datetime(next_open_review),
                                       [next_open_review, work_resource])
        debug_obj.trace(med, ' OpeningHoursCheck scheduled for %s at %s'
                        % (work_resource.name, next_open_review))
    else:
        debug_obj.trace(med, ' OpeningHoursCheck already scheduled for %s at %s'
                        % (work_resource.name, next_open_review))

    return 0


RDC_seqeuence = [('OB',['HMDPT,LOWES,BESTB']),('OB',['_LDC']),('OB',[]),('IB',[])]
FDC_sequence = [('OB',['SEARS,LOWES,BESTB']),('OB',['OTHER']),('OB',['_RDC']),('OB',[]),('IB',[])]



'''
Priority sequence:
RDC Priority:
Outbound: HDA (name contains HMDPT, LOWES, BESTB)
Outbound: LDC Shuttle (name contains _LDC)
Outbound: Other Truck loads (name contains OTHER)
Inbound Priority
Inbound Committed units (items on backorder)
Inbound Other
FDC Priority:
Outbound: HDA (name contains SEARS LOWES, BESTB)
Outbound: Other Truck loads (name contains OTHER)
Outbound: RDC shipment (name contains _RDC)
Inbound Committed units (items on backorder)
Inbound Other
'''

