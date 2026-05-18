# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################

from odoo import api, fields, models, _
from datetime import datetime,date,timedelta
from dateutil.relativedelta import relativedelta
import calendar
import itertools
from operator import itemgetter
import operator
from odoo.exceptions import ValidationError
import calendar


class postpone_installment(models.TransientModel):
    _name = "postpone.installment"
    _description = 'Postpone Installment'
    
    
    postponed_installment_by = fields.Selection([('by_days','By Certain Amount Of Days'),('by_months','By Number of Months'),('by_weeks','By Number of Weeks')]
                                                ,default="by_days"
                                                ,string="Postpone Installment By")
    from_date =  fields.Date('Postpone Installment Since')
    days = fields.Integer('Days to Postpone')
    months = fields.Integer('Months to Postpone')
    weeks = fields.Integer('Weeks to Postpone')
    reason = fields.Text('Reason')
    installment_type = fields.Selection(selection=[('daily', 'Day'),
                                                   ('weekly', 'Week'),
                                                   ('monthly', 'Month'),
                                                   ('quarterly', 'Quarter'),
                                                   ('semiannual', 'Semiannual'),
                                                   ('annual', 'Annual'),
                                                   ], string='Installment Type',default='monthly')
                                                   
                                                   
    @api.onchange('postponed_installment_by')
    def _onchange_postponed_installment_by(self):
        # Reset days/weeks/months values
        self.days = 0
        self.weeks = 0
        self.months = 0

        # Validate incompatible combinations
        if self.installment_type == 'daily' and self.postponed_installment_by in ['by_months', 'by_weeks']:
            self.postponed_installment_by = 'by_days'
            return {
                'warning': {
                    'title': "Invalid Selection",
                    'message': "Postponing by weeks or months is not allowed for daily installments. Reset to 'By Days'."
                }
            }
            

        if self.installment_type == 'weekly' and self.postponed_installment_by == 'by_months':
            self.postponed_installment_by = 'by_weeks'
            return {
                'warning': {
                    'title': "Invalid Selection",
                    'message': "Postponing by months is not allowed for weekly installments. Reset to 'By Weeks'."
                }
            }
            
       
    @api.onchange('installment_type')
    def _onchange_installment_type(self):
        if self.installment_type == 'daily':
            self.postponed_installment_by = 'by_days'
        elif self.installment_type == 'weekly':
            self.postponed_installment_by = 'by_weeks'
        else:
            self.postponed_installment_by = 'by_months'   

    
    def action_postpone_installment(self):
        self.ensure_one()
        loan = self.env['dev.loan.loan'].browse(self._context.get('active_id'))
        if not loan:
            raise ValidationError(_("No active loan found."))

        # Validate postpone method according to installment type
        if self.installment_type == 'daily' and self.postponed_installment_by in ['by_months', 'by_weeks']:
            raise ValidationError(_("You can only postpone by days when the installment type is daily."))
        if self.installment_type == 'weekly' and self.postponed_installment_by == 'by_months':
            raise ValidationError(_("You can only postpone by weeks or days when the installment type is weekly."))

        # Get the installments to update
        installments_to_postpone = loan.installment_ids.filtered(lambda inst: inst.date >= self.from_date and inst.state != 'paid')
        if not installments_to_postpone:
            raise ValidationError(_("No installments found on or after the selected 'Postpone Installment Since' date."))

        # Track changes
        first_changed_date = None
        new_date = None

        for installment in installments_to_postpone:
            if not first_changed_date:
                first_changed_date = installment.date

            if self.postponed_installment_by == 'by_days':
                installment.date += relativedelta(days=self.days)
            elif self.postponed_installment_by == 'by_weeks':
                installment.date += relativedelta(weeks=self.weeks)
            elif self.postponed_installment_by == 'by_months':
                installment.date += relativedelta(months=self.months)

            if not new_date:
                new_date = installment.date

        # Create one record in loan.installment.changes to track this operation
        loan.installment_change_ids.create({
            'date': date.today(),
            'postponed_installment_by': self.postponed_installment_by,
            'days_months': (
                self.days if self.postponed_installment_by == 'by_days'
                else self.weeks if self.postponed_installment_by == 'by_weeks'
                else self.months
            ),
            'reason': self.reason,
            'installment_date': first_changed_date,
            'new_date': new_date,
            'loan_id': loan.id,
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': "Success",
                'message': "Installments postponed successfully.",
                'type': 'success',
                'sticky': False,
            }
        }
        
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    
    
