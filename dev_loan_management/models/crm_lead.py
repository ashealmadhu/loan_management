# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import fields, models, api

class loan_lead(models.Model):
    _inherit = 'crm.lead'
    
    
    def create_loan_request(self):
        vals = {
            'client_id': self.partner_id.id if self.partner_id else False,
            'loan_type_id': self.loan_type_id.id if self.loan_type_id else False,
            'loan_amount': self.loan_amount,
            'installment_limit' : self.loan_term, 
            'lead_id': self.id,
        }
        loan_request = self.env['dev.loan.loan'].create(vals)
        loan_request.onchange_loan_type()
        if loan_request and loan_request.client_id:
            loan_request.client_id.is_allow_loan = True
        return True
        
        
    def _compute_loan_count(self):
        for lead in self:
            loan_ids = self.env['dev.loan.loan'].search([('lead_id','=',self.id)])
            lead.loan_count = len(loan_ids)
            
    def action_view_loan(self):
        action = self.env.ref('dev_loan_management.action_dev_loan_loan').read()[0]
        loan_ids = self.env['dev.loan.loan'].search([('lead_id','=',self.id)])
        if len(loan_ids) > 1:
            action['domain'] = [('id', 'in', loan_ids.ids)]
        elif loan_ids:
            action['views'] = [(self.env.ref('dev_loan_management.view_dev_loan_loan_form').id, 'form')]
            action['res_id'] = loan_ids.id
        return action
            

    loan_type_id = fields.Many2one('dev.loan.type', string='Loan Type')
    loan_amount = fields.Float('Loan Amount')
    loan_term = fields.Integer('Loan Duration')
    loan_id = fields.Many2one('dev.loan.loan',string="Loan")
    loan_count = fields.Integer(string='Loan Request', compute='_compute_loan_count')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
