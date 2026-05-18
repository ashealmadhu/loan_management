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
#from odoo.addons.portal.controllers.mail import _message_post_helper



class CustomerPortal(CustomerPortal):


    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        if  'loan_count' in counters:
        	loan = request.env['dev.loan.loan'].sudo()
        	loan_count =loan.search_count([
		        ('client_id', '=', partner.id),
            ('state', 'not in', ['cancel', 'reject'])
        	])
        	
        	values['loan_count'] = loan_count
        return values
        
        

    
    
    @http.route(['/my/loan', '/my/loan/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_loan(self, page=1, date_begin=None, date_end=None, sortby=None,filterby=None,search=None,search_in='content', groupby='none', **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        loan_pool = request.env['dev.loan.loan']

        today = fields.Date.today()
        this_week_end_date = fields.Date.to_string(fields.Date.from_string(today) + datetime.timedelta(days=7))
        week_ago = datetime.datetime.today() - datetime.timedelta(days=7)
        month_ago = (datetime.datetime.today() - relativedelta(months=1)).strftime('%Y-%m-%d %H:%M:%S')
        starting_of_year = datetime.datetime.now().date().replace(month=1, day=1)    
        ending_of_year = datetime.datetime.now().date().replace(month=12, day=31)

        def sd(date):
            return fields.Datetime.to_string(date)
        def previous_week_range(date):
            start_date = date + datetime.timedelta(-date.weekday(), weeks=-1)
            end_date = date + datetime.timedelta(-date.weekday() - 1)
            return {'start_date':start_date.strftime('%Y-%m-%d %H:%M:%S'), 'end_date':end_date.strftime('%Y-%m-%d %H:%M:%S')}

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'today': {'label': _('Today'), 'domain': [('request_date', '>=', datetime.datetime.strftime(date.today(),'%Y-%m-%d 00:00:00')),('request_date', '<=', datetime.datetime.strftime(date.today(),'%Y-%m-%d 23:59:59'))]},
            'yesterday':{'label': _('Yesterday'), 'domain': [('request_date', '>=', datetime.datetime.strftime(date.today() - datetime.timedelta(days=1),'%Y-%m-%d 00:00:00')),('request_date', '<=', datetime.datetime.strftime(date.today() - datetime.timedelta(days=1),'%Y-%m-%d 23:59:59'))]},
            'week': {'label': _('This Week'),
                     'domain': [('request_date', '>=', sd(datetime.datetime.today() + relativedelta(days=-today.weekday()))), ('request_date', '<=', this_week_end_date)]},
            'last_seven_days':{'label':_('Last 7 Days'),
                         'domain': [('request_date', '>=', sd(week_ago)), ('request_date', '<=', sd(datetime.datetime.today()))]},
            'last_week':{'label':_('Last Week'),
                         'domain': [('request_date', '>=', previous_week_range(datetime.datetime.today()).get('start_date')), ('request_date', '<=', previous_week_range(datetime.datetime.today()).get('end_date'))]},
            
            'last_month':{'label':_('Last 30 Days'),
                         'domain': [('request_date', '>=', month_ago), ('request_date', '<=', sd(datetime.datetime.today()))]},
            'month':{'label': _('This Month'),
                    'domain': [
                       ("request_date", ">=", sd(today.replace(day=1))),
                       ("request_date", "<", (today.replace(day=1) + relativedelta(months=1)).strftime('%Y-%m-%d 00:00:00'))
                    ]
                },
            'year':{'label': _('This Year'),
                    'domain': [
                       ("request_date", ">=", sd(starting_of_year)),
                       ("request_date", "<=", sd(ending_of_year)),
                    ]
                }
        }


        domain = [
            ('client_id', '=', partner.id),
            ('state', 'not in', ['cancel', 'reject'])
        ]

        searchbar_sortings = {
            'name': {'label': _('Name'), 'order': 'name desc'},
            'date': {'label': _('Request Date'), 'order': 'request_date desc'},
            'stage': {'label': _('Stage'), 'order': 'state'},
        }

        searchbar_groupby = {
            'none': {'input': 'none', 'label': _('All')},
            'loan_type_id': {'input': 'session', 'label': _('Loan Type')},
			'state': {'input': 'state', 'label': _('State')},
        }

        if not filterby:
        	filterby = 'all'
        domain += searchbar_filters[filterby]['domain']
        # default sortby order
        if not sortby:
            sortby = 'name'

        sort_order = searchbar_sortings[sortby]['order']

#        archive_groups = self._get_archive_groups('dev.loan.loan', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]
        # count for pager
        loan_count = loan_pool.search_count(domain)
        # make pager

        searchbar_inputs = {
            'name': {'input': 'name', 'label': _('Search in Number')},
			'loan_type_id': {'input': 'loan_type_id', 'label': _('Search in Loan Type')},
			'company_id': {'input': 'company_id', 'label': _('Search in Company')},
			'state': {'input': 'state', 'label': _('Search in State')},
            'all': {'input': 'all', 'label': _('Search in All')},
        }

        	
        if search and search_in:
            search_domain = []
            if search_in in ('name'):
                search_domain =   [('name', 'ilike', search)]  #OR([search_domain, [('name', 'ilike', search)]])
            if search_in in ('loan_type_id'):
                search_domain =   [('loan_type_id', 'ilike', search)]  
            if search_in in ('company_id'):
                search_domain =   [('company_id', 'ilike', search)]
            if search_in in ('state'):
                search_domain =   [('state', 'ilike', search)]             
            if search_in in ('all'):
                search_domain = ['|','|',('name', 'ilike', search),('loan_type_id', 'ilike', search),('company_id', 'ilike', search),('state', 'ilike', search)]
            domain += search_domain 	
        	
        	
        	
		
        pager = portal_pager(
            url="/my/loan",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=loan_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        loan = loan_pool.search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_loan_history'] = loan.ids[:100]
	
        if groupby == 'loan_type_id':
            grouped_loan = [request.env['dev.loan.loan'].concat(*g) for k, g in groupbyelem(loan, itemgetter('loan_type_id'))]
        elif groupby == 'state':
            grouped_loan = [request.env['dev.loan.loan'].concat(*g) for k, g in groupbyelem(loan, itemgetter('state'))]
        else:
            grouped_loan = [loan]

        values.update({
            'date': date_begin,
            'loan': loan.sudo(),
            'page_name': 'loan',
            'pager': pager,
            'default_url': '/my/loan',
			'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,	
			'grouped_loans': grouped_loan,
			'searchbar_groupby':searchbar_groupby,
			'groupby': groupby,
			'searchbar_inputs': searchbar_inputs,
			'search_in': search_in,
			'search': search,
		
        })
        return request.render("dev_loan_management.portal_my_loan", values)
    
    @http.route(['/my/loan/<int:order_id>'], type='http', auth="public", website=True)
    def portal_loan_page(self, order_id, report_type=None, access_token=None, message=False, download=False, **kw):
        try:
            loan_sudo = self._document_check_access('dev.loan.loan', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

            
    	# Check for specific report types and call appropriate report actions
        if report_type == 'report_1':
            # Action for the first report
            return self._show_report(
                model=loan_sudo,
                report_type='pdf',
                report_ref='dev_loan_management.action_print_loan_report',  # Reference to the first report action
                download=download
            )
        elif report_type == 'report_2':
            # Action for the second report
            return self._show_report(
                model=loan_sudo,
                report_type='pdf',
                report_ref='dev_loan_management.action_tmpl_customer_loan_letter',  # Reference to the second report action
                download=download
            ) 
            
        # use sudo to allow accessing/viewing orders for public user
        # only if he knows the private token
        now = fields.Date.today().isoformat()
        # Log only once a day
        if loan_sudo and request.session.get('view_loan_%s' % loan_sudo.id) != now and request.env.user.share and access_token:
            request.session['view_rma_%s' % loan_sudo.id] = now
            body = _('Loan viewed by customer')
#            _message_post_helper(res_model='dev.loan.loan', res_id=loan_sudo.id, message=body, token=loan_sudo.access_token, message_type='notification', partner_ids=loan_sudo.user_id.sudo().partner_id.ids)
            loan_sudo.sudo().message_post(
            body=body,
            message_type='notification',
            subtype_xmlid="mail.mt_note",
            partner_ids=loan_sudo.user_id.sudo().partner_id.ids
            )
        values = {
            'loan': loan_sudo,
            'message': message,
            'page_name': 'loan_order',
            'token': access_token,
            'return_url': '/shop/payment/validate',
            'bootstrap_formatting': True,
            'partner_id': loan_sudo.client_id.id,
            'report_type': 'html',
        }
        if loan_sudo.company_id:
            values['res_company'] = loan_sudo.company_id
        if loan_sudo.state not in ('cancel', 'reject'):
            history = request.session.get('my_loan_history', [])
        else:
            history = request.session.get('my_loan_history', [])
            
        values.update(get_records_pager(history, loan_sudo))
        return request.render('dev_loan_management.loan_portal_template', values)
            
    
    @http.route(['/my/loan/<int:loan_id>/decline'], type='http', auth="public", methods=['POST'], website=True)
    def decline_loan(self, loan_id, access_token=None, **post):
        try:
            loan_sudo = self._document_check_access('dev.loan.loan', loan_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        query_string = False
        if loan_sudo.state == 'draft':
            loan_sudo.action_cancel()
#            _message_post_helper('dev.loan.loan', loan_id, 'Loan Request Cancel', **{'token': access_token} if access_token else {})
            
             # Use the message_post method to log a message
            loan_sudo.message_post(body="Loan Request Cancelled", message_type="notification")
            
        return request.redirect('/my/loan')
        
    
    @http.route(['/my/loan/<int:loan_id>/confirm'], type='http', auth="public", methods=['POST'], website=True)
    def confirm(self, loan_id, access_token=None, **post):
        try:
            loan_sudo = self._document_check_access('dev.loan.loan', loan_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        query_string = False
        if loan_sudo.state == 'draft':
            loan_sudo.action_confirm_loan()
#            _message_post_helper(message='Loan Request Confirm', res_id=loan_id, res_model='dev.loan.loan', **{'token': access_token} if access_token else {})
            
            # Post a confirmation message using message_post
            loan_sudo.message_post(
                body="Loan Request Confirmed",
                message_type="notification",
                subtype_xmlid="mail.mt_note"  # This can be adjusted to the appropriate subtype
            )

        url = loan_sudo.get_portal_url()
        return werkzeug.utils.redirect(url)
        
        

