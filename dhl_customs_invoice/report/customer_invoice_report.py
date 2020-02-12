# coding=utf-8
from odoo import api, models, _
from odoo.exceptions import UserError

class DhlCustomerInvoice(models.AbstractModel):
    _name = "report.dhl_customs_invoice.report_customer_invoice_dhl"

    def get_lines_data(self, inv, delivery):
        line_list = []
        for deliv in delivery.pack_operation_product_ids:
            for line in inv.order_line:
                if line.product_id.id == deliv.product_id.id:
                    tax = 0.0
                    for tax_line in line.tax_id:
                        amount = tax_line.amount
                        tax += amount
                    total = line.price_subtotal * tax / 100
                    line_list.append({
                        'product_id' : line.product_id.code,
                        'product_name' : line.product_id.name,
                        'qty' : deliv.qty_done,
                        'barcode' : line.product_id.barcode,
                        'hs_code' : line.product_id.hs_code,
                        'country_of_origin' : line.product_id.x_Country_of_origin.name,
                        'weight_pr_pc' : line.product_id.weight,
                        'price_unit' : line.price_unit,
                        'tax' : total,
                        'amount_total' : line.price_unit * deliv.qty_done
                    })
        return line_list

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        pickings = self.env['stock.picking'].browse(docids)
        delivery_list = []

        for delivery in pickings:
            invoices = self.env['account.invoice'].search([('origin', 'ilike', delivery.origin)], limit=1, order="id desc")
            sale_order = self.env['sale.order'].search([('name', 'ilike', delivery.origin)])
            if not sale_order:
                raise UserError(_('No Sale Order found as %s order.') % delivery.origin)
            for invoice in sale_order:
                delivery_list.append({
                    'invoice' : invoices.number or '',
                    'name' : invoice.name,
                    'reference' : invoices.name,
                    'due_date' : invoices.date_due,
                    'invoice_date' : invoices.date_invoice,
                    'customer_code' : invoice.partner_id.ref,
                    'incoterms' : invoice.incoterm.code + " - "+ delivery.partner_id.city if invoice.incoterm.id else "",
                    'no_of_colli' : delivery.number_of_packages,
                    'dimensions' : [details.extra_details for details in delivery.tracker_code_ids],
                    'net_weight' : delivery.weight,
                    'gross_weight' : delivery.shipping_weight,
                    'lines' :  self.get_lines_data(invoice, delivery),
                    'currency_id' : invoice.currency_id,
                    'reason_export' : delivery.reason_export,
                    'export_doc_text' : delivery.export_doc_text,
                    
                })

        docargs = {
            'doc_ids' : docids,
            'doc_model' : self.env['stock.picking'],
            'docs' : pickings,
            'datas' : delivery_list,
        }
        return report_obj.render('dhl_customs_invoice.report_customer_invoice_dhl', docargs)