# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import OrderedDict
from odoo.tools import groupby as groupbyelem
from operator import itemgetter
import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import fields, http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.osv.expression import OR
import werkzeug
# from odoo.addons.portal.controllers.mail import _message_post_helper


class CustomerPortal(CustomerPortal):

    @http.route(['/my/loan_request', '/my/loan_request/page/<int:page>'], type='http', auth="public", website=True)
    def create_repair_request(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        loan_details_pool = request.env['dev.loan.type'].sudo()
        domain = [('website','=',True)]
        loan_details = loan_details_pool.search(domain,  limit=self._items_per_page)

        values.update({

            'loan_details': loan_details.sudo(),
            'page_name': 'loan_details_tree',
            'default_url': '/my/loan_request',

        })
        return request.render("dev_loan_management.portal_my_Loan_details", values)

    @http.route('/my/loan_request/<int:loan_id>/view', auth='public', website=True, type='http', csrf_token=True)
    def create_loan_request(self,loan_id,**kw):
        values = self.get_default_data_contact(loan_id)
        return request.render('dev_loan_management.website_loan_requests',values)

    def get_default_data_contact(self,loan_id):
        values = {}
        user_id = request.env['res.users'].sudo().browse(request.uid)
        # loan_type_ids = request.env['dev.loan.type'].sudo().search([])
        # values['loan_type_ids'] = loan_type_ids
        loan_type_ids = request.env['dev.loan.type'].sudo().search([('id', '=', loan_id)]).sudo()
        values['loan_type_ids'] = loan_type_ids
        values['loan_name'] = loan_type_ids.name
        values['loan_amount'] = loan_type_ids.loan_amount
        values['loan_term'] = loan_type_ids.loan_term_by_month
        values['loan_interest_rate'] = loan_type_ids.rate
        values['loan_proof'] = loan_type_ids.proof_ids
        values['loan_eligibility']=loan_type_ids.eligibility_ids
        values['loan_processing_fee']=loan_type_ids.processing_fee

        partner_id=request.env['res.partner'].sudo().search([('id','=',user_id.partner_id.id)])
        if partner_id:
            values['client_id']=partner_id
        values['amount'] = 0.00
        values['term'] = 6
        return values

    
    @http.route(['/dev_loan_management/loan_request_submitted/thank_you'], type='http', auth="public", methods=['POST'], website=True)
    def customer_registration(self, access_token=None, **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.env
		
        loan_type = request.env['dev.loan.type'].browse(int(post['loan_type'])).sudo()

        lead_name = "Enquiry of " + post['name'] + " for " + loan_type.name

        lead_id = pool['crm.lead'].sudo().create({
            'name':  lead_name,
            'contact_name':post['name'],
            'email_from': post['email'],
            'phone': post['mobile'],
            'loan_type_id': loan_type.id,
            'loan_amount': post['amount'],
            'loan_term': post['loan_term'],
            'type': 'lead',
    	})

        return request.render('dev_loan_management.website_loan_thank_you',{'dev_company':lead_id.company_id,'reference_number':lead_id.name})

