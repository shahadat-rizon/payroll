from odoo import fields, models

class HrT4FieldMapping(models.Model):
    _name = 'hr.t4.field.mapping'
    _description = 'T4 Field Mapping'
    _order = 'name'

    name = fields.Char(string='Field Name', required=True)
    field_key = fields.Char(string='Field Key', required=True)
    description = fields.Text(string='Description')