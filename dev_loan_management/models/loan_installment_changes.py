# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import models, fields

class loan_installment_changes(models.Model):
    _name ='loan.installment.changes'
    _description = 'Loan Installment Changes'
    
    date = fields.Date(string='Date of Change')
    postponed_installment_by = fields.Selection([('by_days','By Certain Amount Of Days'),('by_months','By Number of Months'),('by_weeks','By Number of Weeks')]
                                                ,default="by_days"
                                                ,string="Action")
    days_months = fields.Integer('Days/Weeks/Months to Postpone')
    reason = fields.Text('Reason')
    installment_date = fields.Date(string='Installment Date')
    new_date = fields.Date(string='New Date')
    loan_id = fields.Many2one('dev.loan.loan', string='Loan')
          

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
