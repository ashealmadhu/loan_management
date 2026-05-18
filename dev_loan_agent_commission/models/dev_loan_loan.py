# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class dev_loan_loan(models.Model):
    _inherit = "dev.loan.loan"
    _description = "Loan Agent Commission"

    loan_agent_id = fields.Many2one('res.partner', string="Agent", domain=[('is_loan_agent', '=', True)])
    commission_type = fields.Selection(string="Commission Type", selection=[('fixed', 'Fixed'), ('percentage', 'Percentage')], default='fixed')
    commission_fixed_amount = fields.Monetary('Commission Fixed Amount')
    commission_percentage = fields.Float('Commission Percentage')
    commission_count = fields.Integer(compute='_compute_commission_count')

    def _compute_commission_count(self):
        for loan in self:
            loan.commission_count = self.env['agent.commission'].search_count([('loan_id', '=', loan.id)])

    def action_view_commission(self):
        self.ensure_one()
        commissions = self.env['agent.commission'].search([('loan_id', '=', self.id)])
        action = self.env.ref('dev_loan_agent_commission.action_dev_agent_commission').read()[0]
        if len(commissions) > 1:
            action['domain'] = [('id', 'in', commissions.ids)]
        elif len(commissions) == 1:
            action['views'] = [(self.env.ref('dev_loan_agent_commission.view_dev_agent_commission_form').id, 'form')]
            action['res_id'] = commissions.id
        return action

    @api.onchange('loan_agent_id')
    def onchange_loan_agent_id(self):
        if self.loan_agent_id.blacklisted == True:
             warning_mess1 = {
                            'title': _("Warning") ,
                            'message': _("This Agent is blacklisted For This Reason - %s !!") % (self.loan_agent_id.blacklisted_reason)
                            }
             return {'warning': warning_mess1}

    def action_disburse_loan(self):
        res = super(dev_loan_loan, self).action_disburse_loan()
        if self.state == 'disburse' and self.loan_agent_id:
            commission_vals = {
                'agent_partner_id': self.loan_agent_id.id,
                'loan_id': self.id,
                'loan_type_id': self.loan_type_id.id,
                # 'loan_term': self.loan_term,
                'loan_amount': self.loan_amount,
                'total_interest': self.total_interest,
                'start_date': self.disbursement_date,
                'commission_type': self.commission_type,
                'commission_fixed_amount': self.commission_fixed_amount,
                'commission_percentage': self.commission_percentage,
                'state': 'draft',
            }
            self.env['agent.commission'].create(commission_vals)
        return res


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
