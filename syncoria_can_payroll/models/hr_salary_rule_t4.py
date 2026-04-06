from odoo import fields, models

class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    t4_field_mapping_ids = fields.Many2many(
        'hr.t4.field.mapping',
        'salary_rule_t4_mapping_rel',
        'salary_rule_id',
        't4_field_id',
        string='Map to T4 Fields',
        help='Select which T4 fields this salary rule maps to'
    )