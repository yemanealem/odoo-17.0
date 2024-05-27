from odoo import fields, models, api

class physicianPrescription(models.Model):
    _name = "physician.prescription"
    _description = " for phyisician prescription."
    prescription_date = fields.Date(string='Prescription Date')
    physician_id = fields.Many2one('res.partner', string='Physician')
    patient_id = fields.Many2one('res.partner', string='Patient')
    medicine_ids = fields.Many2many(
        comodel_name="product.template",
        required=True,
        string="select_medicine"
    )
