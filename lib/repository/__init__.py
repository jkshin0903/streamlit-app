"""CRUD facade over MariaDB (mng_db), split by domain."""

from ._common import (
    RepositoryError,
    init_if_needed,
    reset_demo_data,
)
from . import (
    business_location,
    contract,
    invoice,
    machine,
    order,
    product,
    purchase_order,
    purchase_request,
    technician,
    vendor,
)
from . import display

# business_location
list_locations = business_location.list_locations
get_location = business_location.get_location
save_location = business_location.save_location
delete_location = business_location.delete_location

# vendor
list_vendors = vendor.list_vendors
get_vendor = vendor.get_vendor
save_vendor = vendor.save_vendor
delete_vendor = vendor.delete_vendor

# product
list_products = product.list_products
get_product = product.get_product
save_product = product.save_product
delete_product = product.delete_product

# technician
list_technicians = technician.list_technicians
get_technician = technician.get_technician
save_technician = technician.save_technician
delete_technician = technician.delete_technician

# contract
list_contracts = contract.list_contracts
get_contract = contract.get_contract
save_contract = contract.save_contract
delete_contract = contract.delete_contract

# machine
list_machines = machine.list_machines
get_machine = machine.get_machine
save_machine = machine.save_machine
delete_machine = machine.delete_machine
list_machine_contract_hst = machine.list_machine_contract_hst
save_machine_contract_hst = machine.save_machine_contract_hst

# order
list_orders = order.list_orders
get_order = order.get_order
save_order = order.save_order
delete_order = order.delete_order

# purchase_request
list_purchase_requests = purchase_request.list_purchase_requests
get_purchase_request = purchase_request.get_purchase_request
list_purchase_request_items = purchase_request.list_purchase_request_items
save_purchase_request = purchase_request.save_purchase_request
delete_purchase_request = purchase_request.delete_purchase_request

# purchase_order
list_purchase_orders = purchase_order.list_purchase_orders
get_purchase_order = purchase_order.get_purchase_order
list_purchase_order_items = purchase_order.list_purchase_order_items
save_purchase_order = purchase_order.save_purchase_order
delete_purchase_order = purchase_order.delete_purchase_order
get_po_vendor_id = purchase_order.get_po_vendor_id

# invoice
list_invoices = invoice.list_invoices
get_invoice = invoice.get_invoice
list_invoice_items = invoice.list_invoice_items
save_invoice = invoice.save_invoice
delete_invoice = invoice.delete_invoice

# display helpers
location_label = display.location_label
vendor_label = display.vendor_label
product_label = display.product_label
technician_label = display.technician_label
id_options = display.id_options
optional_location_options = display.optional_location_options

__all__ = [
    "RepositoryError",
    "init_if_needed",
    "reset_demo_data",
    "list_locations",
    "get_location",
    "save_location",
    "delete_location",
    "list_vendors",
    "get_vendor",
    "save_vendor",
    "delete_vendor",
    "list_products",
    "get_product",
    "save_product",
    "delete_product",
    "list_technicians",
    "get_technician",
    "save_technician",
    "delete_technician",
    "list_contracts",
    "get_contract",
    "save_contract",
    "delete_contract",
    "list_machines",
    "get_machine",
    "save_machine",
    "delete_machine",
    "list_machine_contract_hst",
    "save_machine_contract_hst",
    "list_orders",
    "get_order",
    "save_order",
    "delete_order",
    "list_purchase_requests",
    "get_purchase_request",
    "list_purchase_request_items",
    "save_purchase_request",
    "delete_purchase_request",
    "list_purchase_orders",
    "get_purchase_order",
    "list_purchase_order_items",
    "save_purchase_order",
    "delete_purchase_order",
    "get_po_vendor_id",
    "list_invoices",
    "get_invoice",
    "list_invoice_items",
    "save_invoice",
    "delete_invoice",
    "location_label",
    "vendor_label",
    "product_label",
    "technician_label",
    "id_options",
    "optional_location_options",
]
