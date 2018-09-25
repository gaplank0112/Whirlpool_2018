'''
Script type: OnShipmentArrival
This adds a tag to the shipment designating as an inbound shipment. This becomes necessary in
resource prioritization

'''

import sys
sys.path.append("C:\Python26\SCG_64\Lib")
import sim_server

low, med, high = 2, 5, 9
debug_obj = sim_server.Debug()
model_obj = sim_server.Model()

def main(shipment_obj, mode_obj):
    if mode_obj.lane.destination.objecttype == 'CUSTOMER':
        return

    debug_obj.trace(low, "-" * 30)
    debug_obj.trace(low,"Shipment arrival for %s at %s" % (mode_obj.lane.destination.name, sim_server.NowAsString()))

    shipment_obj.custom1 = 'IB'
