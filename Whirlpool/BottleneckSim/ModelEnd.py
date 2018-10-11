import sys
import sim_server
sys.path.append("C:\Python26\SCG_64\Lib")


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
        debug_obj.trace(low, '%s, time, count %s' % (k, v), 'script_profile.csv')

    # -- Print out all the items stuck in the queue waiting for their order drop date
    debug_obj.trace(low,'Origin, Destination, PromiseDate_ShipCondition, CreateDate, DueDate, DropDate, Reviewed,'
                        'Product, Quantity','queued_orders.csv')
    for site in model_obj.sites:
        for order in site.pendingorders:
            for detail in order.details:
                debug_obj.trace(low,'%s, %s, %s, %s, %s, %s, %s, %s, %s' %
                                (order.orderfromname, order.shiptoname, order.ordernumber, order.datecreated,
                                 order.duedate, order.custom1, order.custom2, detail.productname, detail.quantity),
                                'queued_orders.csv')