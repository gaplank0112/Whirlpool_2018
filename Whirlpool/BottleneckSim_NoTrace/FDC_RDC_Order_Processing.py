# Script Type: Order Queue Review policy
# This script must be applied at all FDC and RDC sites in the User Interface

import sys
import sim_server
import Ship_Conditions
import datetime
import utilities
sys.path.append("C:\Python26\SCG_64\Lib")

low, med, high = 1, 1, 1

debug_obj = sim_server.Debug()
model_obj = sim_server.Model()


def main(site_obj):
    # debug_obj.trace(low, "-" * 30)
    # debug_obj.trace(low, "FDC_RDC_Order processing called at " + sim_server.NowAsString())
    script_start = datetime.datetime.now()
    release_list = []
    error_list = []

    for order_obj in site_obj.pendingorders:
        # -- If this order was previously reviewed, we can skip it. We're just waiting for the time to drop it.
        if order_obj.custom2 == 'REVIEWED':
            # # debug_obj.trace(high, 'Order custom2 == REVIEWED')
            continue
        # -- If the order is going to a inter facility site, we don't need to delay processing - release it immediately
        if order_obj.shipto.objecttype == "SITE":
            release_list.append(order_obj)
            continue

        source, destination_zip, ship_code, destination_name, destination_due_date = get_order_details(order_obj)
        planning_time, trans_lead_time, process_time = \
            get_processing_time(source, ship_code, destination_zip, destination_name, error_list)
        # debug_obj.trace(med, ' Order details: %s, %s, %s, %s, %s, Total process time %s'
        #                % (source, destination_name, destination_zip, ship_code, destination_due_date, process_time))
        # -- Set the priority field to the planning time (the delay time between order drop and ready to ship)
        order_obj.priority = long(planning_time)

        # -- Subtract the processing hours from the lookup from the order's due date
        drop_datetime = destination_due_date - datetime.timedelta(hours=process_time)
        # -- Set the drop_datetime to midnight
        drop_datetime = datetime.datetime(drop_datetime.year, drop_datetime.month, drop_datetime.day)
        current_time = datetime.datetime.utcfromtimestamp(sim_server.Now())
        # debug_obj.trace(med, ' Drop time (due date - total process time) %s' % (drop_datetime))
        # -- Compare the drop date time to the current time - get True or False
        release_order = drop_datetime <= current_time
        # # debug_obj.trace(low,"Drop datetime = %s, current date time = %s, drop order = %s" % \
        #             (drop_datetime, current_time, release_order))

        if release_order is True:
            release_list.append(order_obj)
            # -- Set the custom1 field to note an immediatly dropped order
            order_obj.custom1 = 'IMMEDIATE'
        else:
            sim_server.ScheduleCustomEvent('DropOrder', utilities.str_datetime(drop_datetime), (site_obj, order_obj))
            # # debug_obj.trace(low, 'Custom event scheduled')
            # -- Set the custom1 field to the drop datetime (for tracking)
            # -- Set the custom2 field to REVIEWED so we can skip this order when the queue is reviewed again
            order_obj.custom1 = utilities.str_datetime(drop_datetime)
            order_obj.custom2 = 'REVIEWED'

    # Release any orders that need to drop now
    for order_obj in release_list:
        sim_server.ProcessQueuedOrder(site_obj, order_obj)

    # write out any errors
    if len(error_list) > 0:
        for error in error_list:
            debug_obj.logerror(error)

    utilities.profile_stats('QueuePrioritization', script_start, datetime.datetime.now())


def get_order_details(order_obj):
    sourcename = order_obj.orderfromname
    destinationname = order_obj.shiptoname
    destination_obj = order_obj.shipto
    destination_zip = destination_obj.custom2
    if destination_zip == '':
        debug_obj.logerror('No 3 digit zip in custom 2 field for site/customer %s' % destinationname)
    destination_due_date = order_obj.duedate
    # -- The ordernumber field is a concatenation of promise date and ship condition in format dd/mm/yyyy_ShipCondition
    # -- Ship condition is a 2-digit code at the end of the order number
    promise_date_str, ship_condition = utilities.split_promise_date_ship_condition(order_obj.ordernumber)

    if Ship_Conditions.test_ship_condition(ship_condition) == False:
        ship_condition = Ship_Conditions.main(sourcename, destinationname)
        order_obj.ordernumber = order_obj.ordernumber + "_" + str(ship_condition)
    # # debug_obj.trace(high, "@@@@@@@ ship condition = " + str(ship_condition))
    return sourcename, destination_zip, ship_condition, destinationname, destination_due_date


def get_processing_time(location, ship_condition, three_digit_zip, destination_name, error_list):
    # debug_obj.trace(low, "  Looking for processing time for Location %s, Ship Condition %s, 3 Digit %s "
    #                   "(Destination %s)." % (location, ship_condition, three_digit_zip, destination_name))

    drop_processing_times = model_obj.getcustomattribute("drop_processing_times")
    key = location + "|" + ship_condition + "|" + str(three_digit_zip)
    # debug_obj.trace(high,'   Drop processing lookup key is %s' % key)
    if key in drop_processing_times:
        time = drop_processing_times[key]
    else:
        # TODO: Develop a way to find 'default' numbers based on what we can find
        time = (96.0, 48.0, 144.0)
    # debug_obj.trace(low, "   Time from lookup  " + str(time))
    return time
