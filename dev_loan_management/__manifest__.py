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
    'name': 'Loan Management System in Odoo for Customer and Supplier',
    'version': '19.0.1.3',
    'sequence': 1,
    'category': 'Accounting',
    'description':
        """
This Module help to create loan of customer or Supplier

    """,
    'summary': 'Loan Management system in odoo for customer and supplier, Customer Loan, Supplier Loan, vendor Loan, Loan Type, Loan Proef, Loan type, Loan Request, Notification, Loan Document, Loan installment, Loan Disbursement, Customer Loan Process, Loan emi, Loan summary report',
    'depends': ['crm','mail','account','portal','website','project'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/demo_data.xml',
        'data/cron.xml',
        'edi/mail_template.xml',
        'views/dev_loan_menu.xml',
        'wizard/dev_paid_installment_views.xml',
        'wizard/dev_update_rate_views.xml',
        'wizard/add_advance_payment_views.xml',
        'wizard/generate_agreement.xml',
        'wizard/postpone_installment_view.xml',
        'views/dev_loan_proof_view.xml',
        'views/dev_loan_type.xml',
        'views/res_partner_view.xml',
        'wizard/dev_loan_reject_view.xml',
        'wizard/dev_installment_summary_views.xml',
        'wizard/dev_interest_certificate_views.xml',
        'wizard/create_task.xml',
        'wizard/generate_notice.xml',
        'views/dev_loan_view.xml',
        'views/dev_loan_installment_view.xml',
        'report/report_header.xml',
        'report/report_print_loan.xml',
        'report/installment_summary_template.xml',
        'report/interest_certificate_template.xml',
        'report/outstanding_letter_template.xml',
        'report/report_menu.xml',
        'portal_view/loan_portal_templates.xml',
        'views/borrower_category.xml',
        'views/dev_loan_over_due_installment_view.xml',
        'views/ln_base_document.xml',
        'views/ln_document_type.xml',
        'views/loan_checklist_template.xml',
        'views/co_borrower_relation.xml',
        'views/agreement_type.xml',
        'views/loan_agreement.xml',
        'views/agreement_template.xml',
        'report/report_agreement_template.xml',
        'data/agreement_email.xml',
        'wizard/loan_collection.xml',
        'report/loan_collection_template.xml',
        'wizard/dev_loan_account_summary.xml',
        'views/notice_type.xml',
        'views/loan_notice.xml',
        'views/dev_loan_eligibility_view.xml',
        'data/notice_email.xml',
        'report/report_notice_template.xml',
        'data/overdue_installment_email.xml',
        'views/reminder_days_view.xml',
        'portal_view/portal_loan_agreement_view.xml',
        'portal_view/portal_loan_agreement_sign_view.xml',
        'views/crm_lead.xml',
        'portal_view/loan_details_registration.xml',
        'portal_view/portal_loan_view.xml',
        'portal_view/website_menu.xml',
        'portal_view/loan_notice_portal_templates.xml',
        'views/loan_dashboard.xml',
          
        ],
    'assets': {
            'web.assets_backend': [
                'dev_loan_management/static/src/js/loan_dashboard.js',
                'dev_loan_management/static/src/js/chart_chart.js',
                'dev_loan_management/static/src/css/dashboard_new.css',
                'dev_loan_management/static/src/js/loan_type_validation.js',
                'dev_loan_management/static/src/xml/loan_dashboard_templates.xml',
            ]},
    'demo': [],
    'test': [],
    'css': [],
    'qweb': [],
    'js': [],
    'images': ['images/main_screenshot.gif'],
    'installable': True,
    'application': True,
    'auto_install': False,
    
    # author and support Details =============#
    'author': 'DevIntelle Consulting Service Pvt.Ltd',
    'website': 'http://www.devintellecs.com',    
    'maintainer': 'DevIntelle Consulting Service Pvt.Ltd', 
    'support': 'devintelle@gmail.com',
    'pre_init_hook' :'pre_init_check',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
