import json
from operator import mod
from odoo import fields, models, api
from odoo.exceptions import UserError
from odoo.tools.view_validation import READONLY


class kenema_stock_transfer_custom(models.Model):
    _name = 'kenema.inventory.transfer.custom'
    _description = 'Store Transfer'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', default='New')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),    #When requester cancels it from draft
        ('phmg', 'Supply chain manager'),
        ('waiting', 'Requested'),   #When request is waiting for approval/response
        ('reject', 'Rejected'),     #When request is rejected by issuer store keeper
        ('processed', 'Processed'),  # When request is processed
        ('done', 'Received'),      #When request is received
    ], string='Status', default="draft", readonly=True, tracking=True,
        help=" * Requested: The transfer is requested to the sending warehouse.\n"
             " * Done: The transfer is approved and processed.\n")
    cons_ref = fields.One2many('stock.picking', 'trans_issue_request')
    detail_entries = fields.One2many('kenema.inventory.transfer.custom.detail', 'transfer_header')
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    remark=fields.Char('Remark')
    location_dest_id = fields.Many2one(
        'stock.location', "Destination location",
        required=True,
        state={'draft': [('readonly', False)]})
    location_id = fields.Many2one(
        'stock.warehouse', "Source warehouse")
    store_manager = fields.Many2one('res.users', compute='_get_approvers')
    consignment_item=fields.Boolean(store=True,string='Consignment Item')

    def _get_approvers(self):
        for rec in self:

            if len(rec.detail_entries) > 0:
                rec.store_manager = self.env.ref("kenema_dev.stores_manager").users.ids[0] if len(
                    self.env.ref("kenema_dev.stores_manager").users.ids) > 0 else None

    request_date = fields.Datetime('Request Date', default=fields.Datetime.now,
                                   state={'draft': [('readonly', False)]})

    transfer_reference = fields.Text(string='Request reference', readonly=True)
    transfer_picking=fields.One2many('stock.picking','trans_issue_request',string='Transfer reference')

    @api.model
    def create(self, vals_list):
        if vals_list.get('name', 'New') == 'New':
            if len(vals_list['detail_entries'])==0:
                raise UserError("At least one product must be requested to save record.")
            _name = self.env['ir.sequence'].next_by_code('kenema.inventory.transfer.custom.sequence.all')
            if not _name:
                raise UserError("Request sequence not found.")
            vals_list['name']=_name
        return super(kenema_stock_transfer_custom, self).create(vals_list)

    def action_cancel(self):
        self.state='cancel'

    def reset_order(self):
        self.ensure_one()
        self.set_activity_done()
        self.state = 'draft'
        for rec in self.transfer_picking:
            rec.action_cancel()
    def amend(self):
        self.ensure_one()
        self.set_activity_done()
        self.state = 'draft'


    def request(self):
        self.ensure_one()
        self._get_approvers()
        self.state = 'phmg'

    def phmg_approve(self):
        self.set_activity_done()
        warehouse_list=self.detail_entries['warehouse_id']
        for wh in warehouse_list:
            pick_type_id = self.env['stock.picking.type'].sudo().search(
                [('sequence_code', '=', 'MTOV'),('warehouse_id', 'like', wh.id)]).id
            if not pick_type_id :
                raise UserError("Picking type 'MTOV' is not configured for one of the warehouses.")

        for wh in warehouse_list:
            pick_type_id = self.env['stock.picking.type'].sudo().search(
                [('sequence_code', '=', 'MTOV'), ('warehouse_id', '=', wh.id)]).id
            def_location_id=self.env['stock.location'].search([('usage','=','internal'),('con_type', '=', False),('wcode','=',wh.code)])[0].id
            if not def_location_id:
                raise UserError("Default internal location is not configured for source warehouse.")
            picking_vals = {
                'partner_id': self.company_id.partner_id.id,
                'company_id': self.env.company.id,
                'picking_type_id': pick_type_id,
                'location_id': def_location_id,
                'location_dest_id': self.location_dest_id.id,
                'requested_by': self.create_uid,
                'state': 'draft',
                'trans_issue_request':self.id,
                'scheduled_date': self.request_date
            }
            picking_id = self.env['stock.picking'].sudo().create(picking_vals)

            if not self.transfer_reference:
                self.transfer_reference = picking_id.name + '\n'
            else:
                self.transfer_reference = self.transfer_reference + picking_id.name + '\n'

            for rec in self.detail_entries:

                if(rec['warehouse_id']==wh):
                    move_vals = {
                        'picking_id': picking_id.id,
                        'picking_type_id': pick_type_id,
                        'name': picking_id.name,
                        'product_id': rec['product_id'].id,
                        'product_uom': rec["product_id"].uom_id.id,
                        'product_uom_qty': rec['product_uom_qty']*(rec["product_id"].uom_id.factor/rec["product_uom"].factor),
                        'location_id': def_location_id,
                        'location_dest_id': self.location_dest_id.id,
                        #'state': 'waiting',
                        #'state': 'confirmed',
                        'state': 'draft',
                        'company_id': self.env.company.id
                    }

                    self.env['stock.move'].sudo().create(move_vals)
            picking_id.action_assign()
            picking_id.state='assigned'
        self.state = 'waiting'

    def action_receive(self):
        #for record in self.transfer_picking:
        #    record.button_validate();
        self.state = 'done'

    def set_activity_done(self):
        activity = self.env["mail.activity"].search(
            [('res_name', '=', self.name)])
        for act in activity:
            act.sudo().action_done()
class kenema_stock_transfer_custom_detail(models.Model):
    _name = 'kenema.inventory.transfer.custom.detail'
    transfer_header = fields.Many2one('kenema.inventory.transfer.custom', required=True)

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    location_source_id = fields.Many2one(
        'stock.location', "Source location",
        check_company=True,
        state={'draft': [('readonly', False)]})

    warehouse_id=fields.Many2one(
        'stock.warehouse', "Source warehouse",
        state={'draft': [('readonly', False)]})
    cons_price=fields.Float('Consignment payable')
    @api.depends('location_source_id')
    def _get_wh(self):
        for rec in self:
            rec.warehouse_id=self.env['stock.location'].search([('id','=',rec.location_source_id.id)]).warehouse_id

    product_id = fields.Many2one(
        'product.product', 'Product',
        check_company=True,
        domain="[('type', 'in', ['product', 'consu']), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        index=True, required=True,
        state={'done': [('readonly', True)]})
    product_uom_qty = fields.Float(
        'Request',
        digits='Product Unit of Measure', store=True,
        default=1.0, required=True, state={'done': [('readonly', True)]})
    available_qty = fields.Float('Available', readonly=True, compute="get_count")

    product_uom = fields.Many2one(related='product_id.uom_id', store=True)

    @api.depends('location_source_id', 'product_uom_qty', 'product_id', 'product_uom')
    def get_count(self):
        for rec in self:
            rate = rec.product_uom.factor / (
                rec.product_id.uom_id.factor if rec.product_id.uom_id.factor != 0 else (
                    rec.product_uom.factor if rec.product_uom.factor != 0 else 1))
            rec.available_qty = rec.available_qty + ((self._get_avail_qty_per_warehouse(rec.product_id,
                                                                                           rec.warehouse_id) ))

    def _get_avail_qty_per_warehouse(self, product_id, warehouse_id):

        selfsud = self.sudo()
        tot_quantity = 0.0
        for location_id in selfsud.env['stock.location'].search(
                [('warehouse_id', '=', warehouse_id.id), ('usage', '=', 'internal')]):
            quants = selfsud.env['stock.quant'].search(
                [('product_id', '=', product_id.id), ('location_id', '=', location_id.id)])
            tot_quantity = tot_quantity + sum(quants.mapped('quantity'))
        return tot_quantity

    def set_uom(self):
        pass

    # product_uom = fields.Many2one('uom.uom', "UoM", required=True, domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', store=True)


