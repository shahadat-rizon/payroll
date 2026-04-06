# -*- coding: utf-8 -*-
from odoo import api, fields, models
from lxml import etree


class T4OtherInfoCode(models.Model):
    _name = "syncoria_can_payroll.t4_other_info_code"
    _description = "T4 Other Information (Box–Case) Field Catalog"
    _order = "name, id"
    _rec_name = "name"

    name = fields.Char(required=True, index=True)  # technical field name on statement.remuneration
    field_description = fields.Char()
    ttype = fields.Char(readonly=True)
    relation = fields.Char(readonly=True)
    ir_field_id = fields.Many2one("ir.model.fields", ondelete="cascade", index=True)
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        ("t4_other_info_code_name_uniq", "unique(name)", "Other Info field name must be unique."),
    ]

    @api.model
    def _get_allowed_other_info_field_names_from_view(self):
        """
        Restricted to empl_OTH_INFO group in the T4 form view.
        """
        view = self.env.ref("syncoria_can_payroll.t4_form_view_form", raise_if_not_found=False)
        if not view or not view.arch_db:
            return set()

        root = etree.fromstring(view.arch_db.encode("utf-8"))
        nodes = root.xpath(".//group[@name='empl_OTH_INFO']//field[@name]")
        return {n.get("name") for n in nodes if n.get("name")}

    @api.model
    def sync_from_statement_remuneration_other_info_fields(self):
        """
        Sync catalog from ir.model.fields for statement.remuneration:
        - restrict by allowed names from the empl_OTH_INFO group in the view
        - upsert by ir_field_id or by name
        - archive records no longer in the view
        """
        allowed_names = self._get_allowed_other_info_field_names_from_view()
        if not allowed_names:
            return False

        ir_model = self.env["ir.model"].sudo().search([("model", "=", "statement.remuneration")], limit=1)
        if not ir_model:
            return False

        ir_fields = self.env["ir.model.fields"].sudo().search([
            ("model_id", "=", ir_model.id),
            ("name", "in", list(allowed_names)),
        ])

        existing_by_ir = {
            rec.ir_field_id.id: rec
            for rec in self.sudo().search([("ir_field_id", "!=", False)])
        }
        # Include ALL records (not only ones with ir_field_id) to avoid duplicate key errors
        existing_by_name = {rec.name: rec for rec in self.sudo().search([])}

        seen_names = set()

        for f in ir_fields:
            seen_names.add(f.name)
            vals = {
                "name": f.name,
                "field_description": f.field_description or f.name,
                "ttype": f.ttype,
                "relation": f.relation,
                "ir_field_id": f.id,
                "active": True,
            }

            rec = existing_by_ir.get(f.id) or existing_by_name.get(f.name)
            if rec:
                rec.sudo().write(vals)
            else:
                self.sudo().create(vals)

        to_archive = self.sudo().search([("name", "not in", list(seen_names)), ("active", "=", True)])
        if to_archive:
            to_archive.sudo().write({"active": False})

        return True


class HrSalaryRule(models.Model):
    _inherit = "hr.salary.rule"

    t4_other_info_code_ids = fields.Many2many(
        "syncoria_can_payroll.t4_other_info_code",
        "hr_salary_rule_t4_other_info_code_rel",
        "salary_rule_id",
        "code_id",
        string="T4 Other information (Box–Case)",
        domain=[("active", "=", True)],
        help="Select Other Info (Box–Case) fields this salary rule contributes to.",
    )
