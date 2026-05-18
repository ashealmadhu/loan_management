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


    # def _prepare_home_portal_values(self, counters):
    #     values = super()._prepare_home_portal_values(counters)
    #     partner = request.env.user.partner_id
    #     loan_notice = request.env['ln.notice']
    #     values['loan_notice_count'] = loan_notice.search_count([
    #         ('partner_id', '=', partner.id),
    #     ])
    #     return values

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
    
        if 'loan_notice_count' in counters:
            loan_notice = request.env['ln.notice'].sudo()
            loan_notice_count = loan_notice.search_count([
                ('partner_id', '=', request.env.user.partner_id.id),    	 
            ])
            values['loan_notice_count'] = loan_notice_count
        return values
    
    
    @http.route(['/my/loan_notice', '/my/loan_notice/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_loan_notice(self, page=1, date_begin=None, date_end=None, sortby=None,filterby=None,search=None,search_in=None, groupby='none', **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        loan_pool = request.env['ln.notice'].sudo()

        today = fields.Date.today()
        this_week_end_date = fields.Date.to_string(fields.Date.from_string(today) + datetime.timedelta(days=7))
        week_ago = datetime.datetime.today() - datetime.timedelta(days=7)
        month_ago = (datetime.datetime.today() - relativedelta(months=1)).strftime('%Y-%m-%d %H:%M:%S')
        starting_of_year = datetime.datetime.now().date().replace(month=1, day=1)    
        ending_of_year = datetime.datetime.now().date().replace(month=12, day=31)

    

        domain = [
            ('partner_id', '=', partner.id),
            
        ]

        searchbar_sortings = {
            'name': {'label': _('Name'), 'order': 'name desc'},
            'notice_type_id': {'label': _('Notice Type'), 'order': 'notice_type_id'},
            'loan_id': {'label': _('Loan'), 'order': 'loan_id desc'},
        }

        searchbar_groupby = {
            'none': {'input': 'none', 'label': _('All')},
            'notice_type_id': {'input': 'notice_type_id', 'label': _('Loan Type')},
			'loan_id': {'input': 'loan_id', 'label': _('Loan')},
        }

        if not filterby:
            filterby = 'all'
        
        # default sortby order
        if not sortby:
            sortby = 'name'

        sort_order = searchbar_sortings[sortby]['order']

#        archive_groups = self._get_archive_groups('dev.loan.loan', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]
        # count for pager
        loan_notice_count = loan_pool.search_count(domain)
        # make pager

        searchbar_inputs = {
            'name': {'input': 'name', 'label': _('Search in Number')},
            'loan_id': {'input': 'loan_id', 'label': _('Search in Loan Number')},
			'notice_type_id': {'input': 'notice_type_id', 'label': _('Search in Loan Type')},
            'all': {'input': 'all', 'label': _('Search in All')},
        }

	# search
        # if not search_in:
        #     search_in = 'loan_id'
        # if search and search_in:
        #     search_domain = []
        #     if search_in in ('name', 'all'):
        #         search_domain = OR([search_domain, [('name', 'ilike', search)]])
        #     if search_in in ('loan_id', 'all'):
        #         search_domain = OR([search_domain, [('loan_id', 'ilike', search)]])
        #     if search_in in ('notice_type_id', 'all'):
        #         search_domain = OR([search_domain, [('notice_type_id', 'ilike', search)]])
        	
        #     domain += search_domain

        if search and search_in:
            search_domain = []
            if search_in in ('name'):
                search_domain =   [('name', 'ilike', search)]  #OR([search_domain, [('name', 'ilike', search)]])
            if search_in in ('loan_id'):
                search_domain = [('loan_id', 'ilike', search)]
            if search_in in ('notice_type_id'):
                search_domain = [('notice_type_id', 'ilike', search)]
            if search_in in ('all'):
                search_domain = ['|','|','|','|',('name', 'ilike', search),('loan_id', 'ilike', search),('notice_type_id', 'ilike', search)
                             ]
            domain += search_domain
		
        pager = portal_pager(
            url="/my/loan_notice",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=loan_notice_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        loan_notice = loan_pool.search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])
	
        if groupby == 'loan_id':
            grouped_loan = [request.env['ln.notice'].concat(*g) for k, g in groupbyelem(loan_notice, itemgetter('loan_id'))]
        elif groupby == 'notice_type_id':
            grouped_loan = [request.env['ln.notice'].concat(*g) for k, g in groupbyelem(loan_notice, itemgetter('notice_type_id'))]
        else:
            grouped_loan = [loan_notice]

        values.update({
            'date': date_begin,
            'loan_notice': loan_notice.sudo(),
            'page_name': 'loan_notice_tree',
            'pager': pager,
            'default_url': '/my/loan_notice',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,	
			'grouped_loans': grouped_loan,
			'searchbar_groupby':searchbar_groupby,
			'groupby': groupby,
			'searchbar_inputs': searchbar_inputs,
			'search_in': search_in,
			'search': search,
		
        })
        return request.render("dev_loan_management.portal_my_loan_notice", values)
    
    @http.route(['/my/loan_notice/<int:order_id>'], type='http', auth="public", website=True)
    def portal_loan_notice_page(self, order_id, report_type=None, access_token=None, message=False, download=False, **kw):
        try:
            loan_notice_sudo = self._document_check_access('ln.notice', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        
        # Check for specific report types and call appropriate report actions
        if report_type == 'report_1':
            # Action for the first report
            return self._show_report(
                model=loan_notice_sudo,
                report_type='pdf',
                report_ref='dev_loan_management.action_report_notice',  # Reference to the first report action
                download=download
            )
        
            
        # use sudo to allow accessing/viewing orders for public user
        # only if he knows the private token
        now = fields.Date.today().strftime('%Y-%m-%d')
        # Log only once a day
        if loan_notice_sudo and request.session.get('view_loan_notice%s' % loan_notice_sudo.id) != now and request.env.user.share and access_token:
            request.session['view_rma_%s' % loan_notice_sudo.id] = now
            # body = _('Loan Notice viewed by customer')
            # _message_post_helper(res_model='ln.notice', res_id=loan_notice_sudo.id, message=body, token=loan_notice_sudo.access_token, message_type='notification', partner_ids=loan_notice_sudo.loan_id.user_id.sudo().partner_id.ids)
            author = loan_notice_sudo.partner_id if request.env.user._is_public() else request.env.user.partner_id
            msg = _('Loan Notice viewed by customer %s', author.name)
            loan_notice_sudo.message_post(author_id=author.id, body=msg, message_type='notification', subtype_xmlid="mail.mt_note" , partner_ids=loan_notice_sudo.loan_id.user_id.sudo().partner_id.ids )
        values = {
            'loan_notice_sudo': loan_notice_sudo,
            'message': message,
            'token': access_token,
            'bootstrap_formatting': True,
            'partner_id': loan_notice_sudo.partner_id.id,
            'report_type': 'html',
            'page_name': 'loan_notice_page',
        }
        if loan_notice_sudo.company_id:
            values['res_company'] = loan_notice_sudo.company_id
        
        
        return request.render('dev_loan_management.loan_notice_portal_template', values)
        
    
   
        
        
        

