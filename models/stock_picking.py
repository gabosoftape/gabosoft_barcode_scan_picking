# -*- coding: utf-8 -*-
from odoo import models, api, fields,  _
from odoo.exceptions import UserError, AccessError, ValidationError

class StockPickingBarCode(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    @api.depends('productcodes_ids.bool_barcode','productcodes_ids.qty')
    def _get_picking_checked(self):
        for picking in self:
            if len(picking.productcodes_ids) >= 1 and all(p.bool_barcode for p in picking.productcodes_ids):
                move_products = picking.move_lines.mapped('product_id')
                products = picking.productcodes_ids.mapped('product_id')
                if move_products == products:
                    picking.picking_checked = True

    temp_barcode = fields.Char("Barcode")
    productcodes_ids = fields.One2many('list.productcode', 'picking_id', string='Productos')
    picking_checked = fields.Boolean("Ready Picking", compute="_get_picking_checked")

    @api.onchange('temp_barcode')
    def onchange_temp_barcode(self):
        res = {}
        barcode = self.temp_barcode
        if barcode:
            new_lines = self.env['list.productcode']
            for move in self.move_lines:
                if move.product_id.barcode == barcode:
                    pcode = self.productcodes_ids.filtered(lambda r: r.product_id.id == move.product_id.id)
                    if pcode:
                        pcode.qty += 1.0
                        if pcode.qty > move.product_uom_qty:
                            warning = {
                                'title': _('Warning!'),
                                'message': _('The quantity checked is bigger than quantity in picking move for product %s.'%move.product_id.name),
                            }
                            return {'warning': warning}
                    else:
                        new_line = new_lines.new({
                            'product_id': move.product_id.id,
                            'qty': 1.0,
                        })
                        new_lines += new_line
            self.productcodes_ids += new_lines
            self.temp_barcode = ""

class ListProductcode(models.Model):
    _name = 'list.productcode'

    @api.multi
    @api.depends('qty')
    def _get_bool_barcode(self):
        for record in self:
            move = record.picking_id.move_lines.filtered(lambda r: r.product_id.id == record.product_id.id)
            record.bool_barcode = record.qty == move.product_uom_qty and True or False
    
    barcode = fields.Char('Barcode', related='product_id.barcode')
    default_code = fields.Char('Reference', related='product_id.default_code')
    product_id = fields.Many2one('product.product', string='Product ')
    qty = fields.Float("Quantity",default=1)
    picking_id = fields.Many2one('stock.picking', "Picking", ondelete='cascade')
    bool_barcode = fields.Boolean("Barcode Checked", compute="_get_bool_barcode")
