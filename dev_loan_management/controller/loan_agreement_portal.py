from odoo.addons.portal.controllers.portal import CustomerPortal

from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo import fields, http, _
# from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.osv import expression
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.osv.expression import OR
import werkzeug
from odoo.tools import groupby as groupbyelem
from operator import itemgetter



class CustomerPortal(CustomerPortal):
    # def _prepare_home_portal_values(self, counters):
    #     values = super()._prepare_home_portal_values(counters)
    #     loan_agreement = request.env['ln.agreement']
    #     agreement_count = loan_agreement.search_count([
    #         ('partner_id', '=', request.env.user.partner_id.id),
    #     ])
    #     values['agreement'] = agreement_count
    #     return values

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
    
        if 'agreement_count' in counters:
            loan_agreement = request.env['ln.agreement'].sudo()
            agreement_count = loan_agreement.search_count([
                ('partner_id', '=', request.env.user.partner_id.id),    	 
            ])
            values['agreement_count'] = agreement_count
        return values

        

    @http.route(['/my/agreement_details', '/my/agreement_details/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_loan_agreement(self, page=1, date_begin=None, date_end=None, sortby=None,search=None,search_in=None, groupby='none', **kw):
        values = self._prepare_portal_layout_values()
        agreement_details_pool = request.env['ln.agreement']

        domain = [
            ('partner_id', '=', request.env.user.partner_id.id)
        ]

        searchbar_sortings = {
            'name': {'label': _('Number'), 'order': 'name desc'},
        }
        
        searchbar_groupby = {
            'none': {'input': 'none', 'label': _('All')},
            'loan_id': {'input': 'loan_id', 'label': _('Loan')},
	    'agreement_type_id': {'input': 'agreement_type_id', 'label': _('Agreement Type')},
        }

        # default sortby order
        if not sortby:
            sortby = 'name'
            
        searchbar_inputs = {
            'name': {'input': 'name', 'label': _('Search in Number')},
		     'loan_id': {'input': 'loan_id', 'label': _('Search in Loan')},
		     'agreement_type_id': {'input': 'agreement_type_id', 'label': _('Search in Agreement Type')},
            'all': {'input': 'all', 'label': _('Search in All')},
        }
        
        # search
        # if not search_in:
        #     search_in = 'name'
        # if search and search_in:
        # 	search_domain = []
        # 	if search_in in ('name', 'all'):
        # 		search_domain = OR([search_domain, [('name', 'ilike', search)]])
        # 	if search_in in ('loan_id', 'all'):
        # 		search_domain = OR([search_domain, [('loan_id', 'ilike', search)]])
        # 	if search_in in ('agreement_type_id', 'all'):
        # 		search_domain = OR([search_domain, [('agreement_type_id', 'ilike', search)]])
        # 	domain += search_domain

        if search and search_in:
            search_domain = []
            if search_in in ('name'):
                search_domain =   [('name', 'ilike', search)]  #OR([search_domain, [('name', 'ilike', search)]])
            if search_in in ('loan_id'):
                search_domain = [('loan_id', 'ilike', search)]
            if search_in in ('agreement_type_id'):
                search_domain = [('agreement_type_id', 'ilike', search)]
            if search_in in ('all'):
                search_domain = ['|','|',('name', 'ilike', search),('loan_id', 'ilike', search),('agreement_type_id', 'ilike', search)
                                ]
            domain += search_domain

        sort_agreement_detail = searchbar_sortings[sortby]['order']
        agreement_details = agreement_details_pool.search(domain, order=sort_agreement_detail, limit=self._items_per_page)
        
        if groupby == 'loan_id':
            grouped_loan_agreement = [request.env['ln.agreement'].concat(*g) for k, g in groupbyelem(agreement_details, itemgetter('loan_id'))]
        elif groupby == 'agreement_type_id':
            grouped_loan_agreement = [request.env['ln.agreement'].concat(*g) for k, g in groupbyelem(agreement_details, itemgetter('agreement_type_id'))]
        else:
            grouped_loan_agreement = [agreement_details]


        values.update({
            'date': date_begin,
            'agreement_details': agreement_details.sudo(),
            'page_name': 'agreement_details_tree',
            'default_url': '/my/agreement_details',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'grouped_agreements': grouped_loan_agreement,
	    'searchbar_groupby':searchbar_groupby,
	    'groupby': groupby,
	    'searchbar_inputs': searchbar_inputs,
	    'search_in': search_in,
            'search': search,
        })
        return request.render("dev_loan_management.portal_my_agreement_details", values)

    @http.route(['/my/agreement_details/<int:order_id>'], type='http', auth="public", website=True)
    def portal_loan_agreement_detail_page(self, order_id, report_type=None, access_token=None, message=False, download=False,
                                   **kw):
        try:
            agreement_detail_sudo = self._document_check_access('ln.agreement', order_id,
                                                              access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
            
        if report_type in ('html', 'pdf', 'text'):
                return self._show_report(model=agreement_detail_sudo, report_type=report_type,report_ref='dev_loan_management.action_report_agreement',download=download)
                
        # use sudo to allow accessing/viewing orders for public user
        # only if he knows the private token
        now = fields.Date.today().strftime('%Y-%m-%d')
        # Log only once a day
        if agreement_detail_sudo and request.session.get('view_loan_agreement_%s' % agreement_detail_sudo.id) != now and request.env.user.share and access_token:
            request.session['view_rma_%s' % agreement_detail_sudo.id] = now
            # body = _('Agreement viewed by customer')
            # msg = _('Agreement viewed by customer %s', author.name)
            author = agreement_detail_sudo.partner_id if request.env.user._is_public() else request.env.user.partner_id
            msg = _('Agreement viewed by customer %s', author.name)
            agreement_detail_sudo.message_post(author_id=author.id, body=msg, message_type='notification', subtype_xmlid="mail.mt_note" , partner_ids=agreement_detail_sudo.loan_id.user_id.sudo().partner_id.ids)
            # _message_post_helper(res_model='ln.agreement', res_id=agreement_detail_sudo.id, message=body, token=agreement_detail_sudo.access_token, message_type='notification', partner_ids=agreement_detail_sudo.loan_id.user_id.sudo().partner_id.ids)

        values = {
            'agreement_detail': agreement_detail_sudo,
            'page_name': 'agreement_detail_page',
            'report_type': 'html',
            'token': access_token,
            'bootstrap_formatting': True,
        }
        return request.render('dev_loan_management.portal_my_agreement_detail_form', values)
        
    
    @http.route(['/my/agreement_details/<int:order_id>/accept'], type='json', auth="public", website=True)
    def portal_my_loan_agreement_accept(self, order_id, access_token=None, name=None, signature=None):
        access_token = access_token or request.httprequest.args.get('access_token')
        try:
            loan_agreement_sudo = self._document_check_access('ln.agreement', order_id, access_token=access_token)
        except (AccessError, MissingError): 
            return {'error': _('Invalid Agreement.')}

        if not signature:
            return {'error': _('Signature is missing.')}

        loan_agreement_sudo.write({
            'agreement_signed_by': name,
            'agreement_signed_on': fields.Datetime.now(),
            'agreement_signature': signature,
        })
        request.env.cr.commit()
        
        return {
            'force_refresh': True,
            'redirect_url': loan_agreement_sudo.get_portal_url(),
        }
        
        
        
        
        
        
        
        
        
        
        
        
