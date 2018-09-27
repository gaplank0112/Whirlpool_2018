import sys
import sim_server
import datetime
import utilities
sys.path.append("C:\Python26\SCG_64\Lib")

low, med, high = 2, 2, 2
debug_obj = sim_server.Debug()
model_obj = sim_server.Model()


def main(work_resource):
    debug_obj.trace(low,'-'*30)
    debug_obj.trace(low,'Queue prioritization called at ' + sim_server.NowAsString())
    script_start = datetime.datetime.now()
    # -- Set up a temporary container to hold results of is_open queries to avoid looping multiple times
    is_open_dict = {}
    site_obj = work_resource.owner
    consumer_queue = work_resource.waitingconsumerqueue
    debug_obj.trace(low, ' At site %s, resource name %s' % (site_obj.name, work_resource.name))
    debug_obj.trace(low, '  Units - utilized %s, available %s, total %s'
                   % (work_resource.utilizedunits, work_resource.availableunits, work_resource.unitcount))
    debug_obj.trace(low, '  Queue size = %s' % len(consumer_queue))

    if work_resource.availableunits == 0:
        debug_obj.trace(low,'  No available resources. Skipping this prioritization')
        return

    # -- Create a sorted list of items on back order. This is used to prioritize inbound shipments waiting for unload
    back_order_list = []
    for site_product in site_obj.products:
        if site_product.currentorderquantity > 0.0:
            back_order_list.append((site_product.product.name, site_product.currentorderquantity))
    back_order_sort = sorted(back_order_list, key=lambda a: a[1], reverse=True)  # -- Sort by the second element in the tuple
    debug_obj.trace(low,'TESTING DELETE sorted back orders %s' % back_order_sort)

    if len(consumer_queue) > 0:
        try:
            open_booleans = is_open_dict[site_obj.name]
            is_open_receiving, is_open_shipping = open_booleans[0], open_booleans[1]
        except:
            is_open_receiving, is_open_shipping = open_hours(site_obj,
                                                             datetime.datetime.utcfromtimestamp(sim_server.Now()))
            # -- Add the results of the is_open query to the dictionary
            is_open_dict[site_obj.name] = (is_open_receiving, is_open_receiving)
        debug_obj.trace(med, '   Site is open receiving = %s, is open shipping = %s /n'
                        % (is_open_receiving, is_open_shipping))
        if is_open_shipping == False and is_open_receiving == False:
            return # -- The site is closed so no reason to prioritize anything now.

        # -- Filter out any items that can not be released
        filtered_queue = filter_consumer_queue(consumer_queue, is_open_receiving, is_open_shipping,
                                               is_open_dict, work_resource)
        # -- Sort the queue by the prioritization sequence
        # -- NOTE: A hard sequence provided here but allows the user to change the sequence later
        sequence = []
        filtered_queue = prioritize_queue('FDC', filtered_queue, sequence)
        # filtered_queue = filtered_queue.sort(priority, longest_time_in_queue)

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

    utilities.profile_stats('QueuePrioritization', script_start, datetime.datetime.now())



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
    prioritization_queue = []
    # is the site open for receiving? If not, remove all inbound shipments
    for consumer in queue:
        debug_obj.trace(med,' Evaluating queued item type %s' % consumer.objecttype)
        shipment_type = get_shipment_type(consumer)
        debug_obj.trace(med, '  Shipment type %s, origin %s, destination %s'
                        % (shipment_type, consumer.items[0].orderfromname, consumer.items[0].shiptoname))
        add_item = []
        add_item.append(check_for_objecttype(consumer))
        add_item.append(check_receiving_open(shipment_type, open_receiving))
        add_item.append(check_open_outbound(shipment_type, open_shipping))
        add_item.append(check_delivery_open(shipment_type, consumer, is_open_dict, work_resource))
        debug_obj.trace(high,'      Type=Shipment? %s | IB:source recv open? %s | OB:source ship open? %s | '
                             'OB:open at delivery? %s' % (add_item[0], add_item[1], add_item[2], add_item[3]))
        add_item = [x for x in add_item if x is not None] # remove any None items from the True/False list

        if all(add_item): #if everything is True, add the item
            prioritization_queue.append(consumer)

    return prioritization_queue


def get_shipment_type(consumer):
    if consumer.custom1:  # we tag inbound items as they arrive. If the item isn't tagged, it must an outbound
        shipment_type = consumer.custom1
    else:
        shipment_type = 'OB'
        consumer.custom1 = shipment_type
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
    if shipment_type == 'OB':
        site_obj = consumer.items[0].shipto
        try:
            open_booleans = is_open_dict[site_obj.name]
            is_open_receiving, is_open_shipping = open_booleans[0], open_booleans[1]
        except:
            # -- Calculate the expected delivery date as current time + transit time from Drop Processing Order table
            transit_time = 48.0
            # TODO: transit_time = site_obj.getcustomattribute('Transit_Time')
            expected_delivery = datetime.datetime.utcfromtimestamp(sim_server.Now()) + \
                                datetime.timedelta(hours=transit_time)
            is_open_receiving, is_open_shipping = open_hours(site_obj, expected_delivery)
            # -- Add the results of the is_open query to the dictionary
            is_open_dict[site_obj.name] = (is_open_receiving, is_open_receiving)

            if is_open_receiving is False: # -- We need to schedule a resource check when the receive window opens
                schedule_resource_check(site_obj, expected_delivery, work_resource)

        return is_open_receiving


def prioritize_queue(site_type, queue, sequence):
    # create a list of all items on backorder
    # check the item for priority already attached
    # walk through the sequence. Determine which index applies.
    # add to priority field.

    return queue


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

