from odoo import  models,fields

class kenema_stock_picking_extension(models.Model):
    _inherit = 'stock.picking'

    trans_issue_request=fields.Many2one('kenema.inventory.transfer.custom','Transfer request')
class kenema_warehouse_extension(models.Model):
    _inherit = 'stock.warehouse'
    has_dispensary_location = fields.Boolean("Has dispensary location")
class kenema_location_extension(models.Model):
    _inherit = 'stock.location'
    con_type = fields.Selection([
        ('SRL', 'Inter-store receive transit location'),
        ], string='Cons/sample Type')
    wcode=fields.Char(related='warehouse_id.code')

    has_read_access = fields.Boolean('is_loc_accessible', default=False, compute='_compute_has_read_access',
                                     search='_search_has_read_access')
    def _search_has_read_access(self, operator, value):

        compiled_wh_domain=self.env.user.warehouse_ids_ph.mapped('code')

        if operator == '=':
            if len(compiled_wh_domain) == 0 or not self.env.user.has_group('kenema_dev.inventory_report'):
                return [('id', 'in', [])]
            else:
                has_read_access=self.env['stock.location']
                has_read_access= self.env['stock.location'].sudo().search(
                    [('wcode', 'in', compiled_wh_domain)])

                return [('id', 'in', [x.id for x in has_read_access] if has_read_access else False)]
        else:
            return [('id', 'in', [])]

    def _compute_has_read_access(self):
        compiled_wh_domain=self.env.user.warehouse_ids_ph.mapped('code')

        for rec in self:
            if rec.wcode in compiled_wh_domain and self.env.user.has_group('kenema_dev.inventory_report'):
                rec.has_read_access = True
            else:
                rec.has_read_access = False

    has_access = fields.Boolean('is_loc_accessible', default=False, compute='_compute_has_access',
                                search='_search_has_access')

    def _search_has_access(self, operator, value):

        compiled_wh_domain=self.env.user.warehouse_ids_ph.mapped('code')

        if operator == '=':
            if len(compiled_wh_domain) == 0:
                return [('id', 'in', [])]
            else:
                has_access=self.env['stock.location']
                if self.env.user.has_group('kenema_dev.inventory_stk'):
                    has_access+= self.env['stock.location'].sudo().search(
                        [('wcode', 'in', compiled_wh_domain) ,('con_type','!=','DIL')])
                if self.env.user.has_group('kenema_dev.inventory_dm') :
                    has_access+= self.env['stock.location'].sudo().search(
                        [('wcode', 'in', compiled_wh_domain), ('con_type', '=', 'DIL')])

                return [('id', 'in', [x.id for x in has_access] if has_access else False)]
        else:
            return [('id', 'in', [])]

    def _compute_has_access(self):
        compiled_wh_domain=self.env.user.warehouse_ids_ph.mapped('code')

        for rec in self:
            if rec.wcode in compiled_wh_domain and ((self.env.user.has_group('kenema_dev.inventory_dm') and rec.con_type=='DIL') or
                                                    (self.env.user.has_group('kenema_dev.inventory_stk') and rec.con_type!='DIL')):
                rec.has_access = True
            else:
                rec.has_access = False

class ResUsers(models.Model):
    _inherit = 'res.users'

    warehouse_ids_ph = fields.Many2many('stock.warehouse', 'stock_warehouse_access_ph', 'uid', 'warehouse_id',
                                           string='Stock warehouse access')


class droga_stock_picking_type_extension(models.Model):
    _inherit = 'stock.picking.type'
    warehouse_code=fields.Char(related='warehouse_id.code',store=True)


    has_access=fields.Boolean('is_type_accessible',default=False,compute='_compute_has_access',search='_search_has_access')

    def _search_has_access(self, operator, value):

        compiled_wh_domain = self.env.user.warehouse_ids_ph.mapped(
            'code')

        if operator=='=':
            if len(compiled_wh_domain)==0:
                return [('id','in',[])]
            else:
                has_access = self.env['stock.picking.type']
                if self.env.user.has_group('kenema_dev.inventory_stk'):
                    has_access+=self.env['stock.picking.type'].sudo().search([('warehouse_code','in',compiled_wh_domain)])

                return [('id', 'in', [x.id for x in has_access] if has_access else False)]
        else:
            return [('id','in',[])]

    def _compute_has_access(self):
        compiled_wh_domain = self.env.user.warehouse_ids_ph.mapped(
            'code')

        for rec in self:
            if rec.warehouse_code in compiled_wh_domain:
                rec.has_access=True
            else:
                rec.has_access=False
                
class droga_stock_picking_extension(models.Model):
    _inherit = 'stock.picking'
    has_access=fields.Boolean('is_pick_accessible', default=False, compute='_compute_has_access',
                                search='_search_has_access')
    def _search_has_access(self, operator, value):

        if operator == '=':
            has_access = self.env['stock.picking'].sudo().search(
                #['|',('location_id.has_access', '=', True),('location_dest_id.has_access', '=', True)])
                ['|','&', ('location_id.has_access', '=', True),('location_id.con_type', '!=', 'SRL'), '&',('location_dest_id.con_type', '!=', 'SRL'),('location_dest_id.has_access', '=', True)])

            if self.env.user.has_group('kenema_dev.inventory_dmi'):
                has_access += (self.env['stock.picking'].sudo().search([('picking_type_id.dispatch_location', '=', 'IM')]))
            if self.env.user.has_group('kenema_dev.inventory_dmw'):
                has_access += (self.env['stock.picking'].sudo().search([('picking_type_id.dispatch_location', '=', 'WS')]))


            return [('id', 'in', [x.id for x in has_access] if has_access else False)]
        else:
            return [('id', 'in', [])]
        
        
    def _compute_has_access(self):
        compiled_wh_domain = []
        user_groups_list = self.env.user.groups_id
        for user_group in user_groups_list:
            given_ules = user_group.rule_groups
            for rule in given_ules:
                if 'Warehouse' in rule.model_id.name:
                    compiled_wh_domain.append(
                        rule.domain_force.strip().replace("[('code', '=', ", '').replace("'", '').replace(')]', ''))

        for rec in self:

            if rec.location_id.has_access or rec.location_dest_id.has_access:
                rec.has_access = True
            else:
                rec.has_access = False