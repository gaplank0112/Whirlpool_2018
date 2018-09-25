import datetime

class Site:
    def __init__(self, siteName):
        self.name = siteName
        productTuple = (SiteProduct(self, "Product1"), SiteProduct(self, "Product2"))
        self.products = productTuple
        orderTuple = (Order(), Order())
        shipmentTuple = (Shipment(),Shipment())
        self.pendingorders = orderTuple
        self.backorders = orderTuple
        self.latitude = 0.0
        self.longitude = 0.0
        self.inventoryweight = 0.0
        self.inventoryvolume = 0.0
        self.inventoryvalue = 0.0
        self.inventorycarryingcostrate = 0.0
        self.isgroup = False
        self.operatingstate = 1
        self.orderhandlingwhendown = 1
        self.shipmenthandlingwhendown = 1
        self.pendingordercount = 1
        self.productionorders = orderTuple
        self.componentorders = orderTuple
        self.pendinginboundshipmentcount = 1
        self.pendingoutboundshipmentcount = 1
        self.pendinginboundshipments = shipmentTuple
        self.pendingoutboundshipments = shipmentTuple
        self.custom1 = "string1"
        self.custom2 = "string2"
        self.workcenters = (WorkCenter(),WorkCenter())
        self.workresources = (WorkResource(), WorkResource())


class Product:
    def __init__(self, productName):
        self.name = productName
        self.cost = 0.0
        self.value = 0.0
        self.volume = 0.0
        self.weight = 0.0
        self.price = 0.0
        self.myvalue = True

class SiteProduct:
    def __init__(self,Site, productName):
        self.site = Site
        self.product = Product(productName)
        self.quantityInStock = 0
        self.quantityOnOrder = 0
        self.quantityOnBackOrder = 0
        self.reorderPoint =50
        self.reorderQuantity = 100
        self.sourcingPolicy = 1

class Order:
    def __init__(self):
        self.totalquantity = 0
        detailTuple = (OrderDetail(), OrderDetail())
        self.details = detailTuple
        self.detail = OrderDetail()
        self.datecreated = datetime.date

class OrderDetail:
    def __init__(self):
        self.quantity = 0

class Shipment:
   def __init__(self):
       self.totalquantity = 0.0

class Lane:
    def __init__(self, laneName):
        self.name = laneName
        modeTuple = (Mode(), Mode())
        self.modes = modeTuple
        self.totalweightpendingmode = 0.0
        self.totalvolumependingmode = 0.0
        self.totalquantitypendingmode = 0.0
        self.pendingmodequeue = ConsignmentList()

    def setmode(self,modename):
        return 0


class ShippingItem:
    def __init__(self):
        self.totalquantity =0


class ConsignmentList:
    def __init__(self):
        self.totalquantity = 0.0
        self.count = 1
        self.totalweight = 0.0
        self.totalvolume = 0.0
        shippingItems = (ShippingItem(), ShippingItem())
        self.items = shippingItems

class Mode:
    def __init__(self):
        self.name = ""
        self.modeparameter = 15

class WorkCenter:
    def __init__(self):
        self.name = ""

class WorkResource:
    def __init__(self):
        self.name = ""

def CreateProductionOrder(productName, reorderQuantity, siteName):
    return 0

def CreateOrder(productName, reorderQuantity, siteName):
    return 0

class Model:
    def __init__(self):
        self.name = ""

class Debug:
    def __init__(self):
        self.name = ""

    def trace(self,level,msg):
        if level == 5 :
            print str(msg)