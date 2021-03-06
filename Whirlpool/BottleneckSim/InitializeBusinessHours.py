__version__ = '1.0'
__author__ = 'Greg Plank'

import sys
import sim_server
from csv import reader
import datetime
import utilities
from Class_Info import BusinessHours
sys.path.append("C:\Python26\SCG_64\Lib")

low, med, high = 2, 5, 9
debug_obj = sim_server.Debug()
model_obj = sim_server.Model()


def main():
    """
    This module reads the business hours table, adds the data to a BusinessHours object and places that on the
    applicable object as a custom attribute. The module also does a look up using the sites table to find the
    UTC offset. The assumption is that the hours in the Business Hours input is in local time.

    "SitesTable","String","@Table:Sites","9999",
    "CustomersTable","String","@Table:Customers","9999",
    """
    debug_obj.trace(low, " Initialize Business Hours called at " + sim_server.NowAsString())
    script_start = datetime.datetime.now()
    apply_business_hours_attribute()
    set_business_hours()
    get_site_timezone()
    get_customer_timezone()
    trace_details()
    debug_obj.trace(low, " Initialize Business Hours complete\n")

    # -- Collect usage stats of the scripts for profiling
    utilities.profile_stats('InitializeBusinessHours', script_start, datetime.datetime.now())


def apply_business_hours_attribute():
    """
    Loop through each site, workcenter, workresource and customer. Use apply_bh to add a BusinessHours class object
    """
    for site_obj in model_obj.sites:
        apply_bh(site_obj)
        for work_center_obj in site_obj.workcenters:
            apply_bh(work_center_obj)
        for work_resources_obj in site_obj.workresources:
            apply_bh(work_resources_obj)
    for customer_obj in model_obj.customers:
        apply_bh(customer_obj)


def apply_bh(object_obj):
    """
    Adds a BusinessHours object to the input object
    :param object_obj:
    """
    bh = BusinessHours(object_obj.name)
    object_obj.setcustomattribute("BusinessHours", bh)


def get_site_timezone():
    """
    This function reads and applies time zone offsets from the sites table.
    It requires a global variable in the UI input - @Table:Sites.
        "Name","Type","Value","Dimensions","Notes"
        "Sites","String","@Table:Sites","9999"
    """
    debug_obj.trace(low, "\n Get site timezone called at " + sim_server.NowAsString())

    # Set this variable to the name of the input file
    filename = "sites.txt"
    datafile = model_obj.modelpath + '\\' + filename

    t = open(datafile)
    csv_t = reader(t, delimiter=',')

    for row in csv_t:
        site_name = row[1].upper()
        # -- Because the table is parsed by commas, the index for the time zone could change. We have to find a
        # -- common starting point in order to find the time zone field
        try:
            idx = int(row.index('10 year Straight-line')) - 2
        except ValueError:
            idx = 31
        site_tz = row[idx]
        if 'Include' in row or 'INCLUDE' in row:
            debug_obj.trace(high, "    Name %s, TZ %s" % (site_name, site_tz))
            if site_tz == "":
                debug_obj.logerror("Null time zone for location %s. Setting time zone to UTC" % site_name)
                site_tz = "UTC"

            # -- Get the time zone and DST flag from the list in the utilities module
            # -- Set the time zone and DST flag in business hours object of the current location
            tz_offset, dst_status = utilities.get_timezone_offset(site_tz)
            site_obj = utilities.get_object(site_name)
            bh = site_obj.getcustomattribute("BusinessHours")
            bh.utc_offset = tz_offset
            bh.observe_daylight_savings = dst_status
            site_obj.setcustomattribute("BusinessHours", bh)


def get_customer_timezone():
    """
    This function reads and applies time zone offsets from the customers table.
    It requires a global variable in the UI input - @Table:Customers.
        "Name","Type","Value","Dimensions","Notes"
        "Customers","String","@Table:Customers","9999"
    """
    debug_obj.trace(low, "\n Get customer time zone called at " + sim_server.NowAsString())

    # Set this variable to the name of the input file
    filename = "customers.txt"
    datafile = model_obj.modelpath + '\\' + filename

    # go through and schedule all state changes
    t = open(datafile)
    csv_t = reader(t, delimiter=',')

    for row in csv_t:
        site_name = row[1].upper()
        site_tz = row[19]
        if 'Include' in row or 'INCLUDE' in row:
            debug_obj.trace(high, "    Name %s, TZ %s" % (site_name, site_tz))
            if site_tz == "":
                debug_obj.logerror("Null time zone for location %s. Setting time zone to UTC" % site_name)
                site_tz = "UTC"

            # -- Get the time zone and DST flag from the list in the utilities module
            # -- Set the time zone and DST flag in business hours object of the current location
            tz_offset, dst_status = utilities.get_timezone_offset(site_tz)
            site_obj = utilities.get_object(site_name)
            bh = site_obj.getcustomattribute("BusinessHours")
            bh.utc_offset = tz_offset
            bh.observe_daylight_savings = dst_status
            debug_obj.trace(high, '     Business hours attributes set for %s' % site_name)


def set_business_hours():
    """
    This function reads and applies business hours informmation to objects.
    It requires a global variable in the UI input - @Table:OpenHourLocation.
        "Name","Type","Value","Dimensions","Notes"
        "BusinessHours","String","@Table:OpenHourLocation","9999"
    """
    debug_obj.trace(low, "  Set business hours called at " + sim_server.NowAsString())

    # Set this variable to the name of the input file
    filename = "openhourlocation.txt"
    datafile = model_obj.modelpath + '\\' + filename
    t = open(datafile)
    csv_t = reader(t, delimiter=',')

    #ID,sun_open,sun_close,mon_open,mon_close,tue_open,tue_close,wed_open,wed_close
    #thu_open,thu_close,fri_open,fri_close,sat_open ,sat_close,status,site_name
    for row in csv_t:
        operating_hours = [row[1],row[2],row[3],row[4],row[5],row[6],row[7],
                           row[8],row[9],row[10],row[11],row[12],row[13],row[14]]
        object_name = row[16]
        bh_type = row[17].upper()
        bh_type = bh_type.strip()
        this_obj = utilities.get_object(object_name)
        if row[15].upper() == 'INCLUDE':
            business_hours = this_obj.getcustomattribute("BusinessHours")
            business_hours.operating_hours[bh_type] = operating_hours
            debug_obj.trace(med, "   Adding hours to %s" % this_obj.name)
            debug_obj.trace(high,"    %s: Hours %s" % (bh_type, operating_hours))


def trace_details():
    """
    This function writes details to scriptlog.txt from the Business Hours class attached to each site, work center,
    work resource and customer if the trace level in the UI options is set to high. It's main purpose is
    troubleshooting to see what the program sees after the initialization process is complete
    """
    debug_obj.trace(high, "\n Printing out business hours info")
    for site_obj in model_obj.sites:
        trace_bh(site_obj)
        for work_center_obj in site_obj.workcenters:
            trace_bh(work_center_obj)
        for work_resources_obj in site_obj.workresources:
            trace_bh(work_resources_obj)
    for customer_obj in model_obj.customers:
        trace_bh(customer_obj)


def trace_bh(obj):
    """
    This function accepts a site, work center, work resource or customer object and prints to the scriptlog.txt
    the business hours details of operating hours, UTC offset and DST observance
    :param obj: site, work center, work resource or customer
    """
    debug_obj.trace(high, "  %s: %s" % (obj.objecttype, obj.name))
    bh_data = obj.getcustomattribute("BusinessHours")
    debug_obj.trace(high, "   Open hours " + str(bh_data.operating_hours))
    debug_obj.trace(high, "   UTC offset " + str(bh_data.utc_offset))
    debug_obj.trace(high, "   Observe DST? " + str(bh_data.observe_daylight_savings))




if __name__ == "__main__":
    main()

