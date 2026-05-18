# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

{
    'name': 'Loan Agent Commission',
    'version': '19.0.1.0',
    'sequence': 1,
    'category': 'Loan',
    'description':
        """
        This Module help to create loan agent commission

    """,
    'summary': 'Loan Agent Commission',
    'author': 'Devintelle Consulting Service Pvt.Ltd',
    'website': 'http://www.devintellecs.com',
    'depends': ['dev_loan_management'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/res_partner_view.xml',
        'views/dev_loan_view.xml',
        'views/dev_loan_type_view.xml',
        'views/agent_commission.xml',        
        ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'pre_init_hook' :'pre_init_check',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
