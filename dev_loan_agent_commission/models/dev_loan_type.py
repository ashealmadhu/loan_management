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

class dev_loan_type(models.Model):
    _inherit = "dev.loan.type"
    _description = "Loan Type Agent Commission"

    agent_commission_product_id = fields.Many2one('product.product', string='Agent Commission')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
