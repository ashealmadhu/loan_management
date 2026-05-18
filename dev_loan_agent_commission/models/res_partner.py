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

class res_partner(models.Model):
    _inherit = "res.partner"
    
    is_loan_agent = fields.Boolean('Loan Agent')
    blacklisted = fields.Boolean('Blacklisted Agent')
    blacklisted_reason = fields.Text('Blacklist Reason ')
    count_loan_agent = fields.Integer('View Agent Loan', compute='_count_loan_agent')
    
            
    def _count_loan_agent(self):
        counter=0 
        for rec in self:
            loan_ids = self.env['dev.loan.loan'].search([('loan_agent_id','=',self.id),('state','not in',['draft','reject','cancel'])])
            list_id = loan_ids.ids
            counter = len(list_id)
        rec.count_loan_agent = counter        
            
    def action_view_loan_agent(self):
        loan_ids = self.env['dev.loan.loan'].search([('loan_agent_id','=',self.id)])
        if loan_ids:
            action = self.env.ref('dev_loan_management.action_dev_loan_loan').read()[0]
            action['domain'] = [('id', 'in', loan_ids.ids),('state','not in',['draft','reject','cancel'])]
            return action
        else:
            action = {'type': 'ir.actions.act_window_close'}   
             

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

