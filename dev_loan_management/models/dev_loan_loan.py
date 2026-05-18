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
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
from odoo.exceptions import RedirectWarning
from odoo.tools import format_date


class dev_loan_loan(models.Model):
    _name = "dev.loan.loan"
    _inherit = ['mail.thread', 'mail.activity.mixin','portal.mixin']
    _order = 'name desc'
    _description = "Loan"
    
    name = fields.Char('Name', default='/', copy=False)
    client_id = fields.Many2one('res.partner', domain=[('is_allow_loan','=',True)], required="1", string='Borrower')
    request_date =fields.Date('Request Date', default=fields.Date.today(), required="1")
    approve_date = fields.Date('Approve Date', copy=False)
    disbursement_date = fields.Date('Disbursement Date', copy=False)
    loan_type_id = fields.Many2one('dev.loan.type', string='Loan Type', required="1")
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    loan_amount = fields.Monetary('Loan Amount', required="1")
    is_interest_apply = fields.Boolean(related='loan_type_id.is_interest_apply', string='Apply Interest')
    interest_rate = fields.Float(string='Interest Rate')
    none_interest_month = fields.Integer(string='None Interest Month')
    loan_term = fields.Integer('Loan Term')
    interest_mode = fields.Selection([('flat','Flat'),('reducing','Reducing')], string='Interest Mode')
    
    state = fields.Selection([('draft','Draft'),
                              ('confirm','Confirm'),
                              ('approve','Approve'),
                              ('disburse','Disburse'),
                              ('open','Open'),
                              ('close','Close'),
                              ('cancel','Cancel'),
                              ('reject','Reject')], string='Status', required="1", default='draft',tracking=1)
    
    
    installment_ids = fields.One2many('dev.loan.installment','loan_id', string='Installments')
    
    total_interest = fields.Monetary('Interest Amount', compute='get_total_interest')
    paid_amount = fields.Monetary('Paid Amount', compute='get_total_interest')
    remaing_amount = fields.Monetary('Remaining Amount', compute='get_total_interest')
    total_estimated_paid_amount = fields.Monetary('Total Estimated Amount To Pay', compute='get_total_estimated_paid_amount')
    notes = fields.Text('Notes')
    reject_reason = fields.Text('Reject Reason', copy=False)
    reject_user_id = fields.Many2one('res.users','Reject By', copy=False)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self:self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self:self.env.user.company_id.currency_id.id)
    proof_ids = fields.Many2many('dev.loan.proof', string='Loan Proof') 
    loan_account_id = fields.Many2one('account.account', string='Disburse Account')
    interest_account_id = fields.Many2one('account.account', string='Interest Account', related='loan_type_id.interest_account_id', readonly=True)
    tds_account_id = fields.Many2one('account.account', string='TDS Account', related='loan_type_id.tds_account_id', readonly=True)
    disburse_journal_id = fields.Many2one('account.journal', string='Disburse Journal')
    disburse_journal_entry_id = fields.Many2one('account.move', string='Disburse Account Entry', copy=False)
    loan_document_ids = fields.One2many('ir.attachment','res_id', string='Loan Document',
                                            domain=[('document_type','=','loan')],
                                            context={
                                            'default_res_model': 'dev.loan.loan',
                                            'default_res_id': lambda self: self.id,
                                            'default_document_type': 'loan',
                                        })
    attachment_number = fields.Integer(compute='_compute_attachment_number', string='Number of Attachments')
    emi_estimate = fields.Monetary(string="Estimated Monthly Payment", compute="_estimated_monthly_payment")
    adv_payment_lines = fields.One2many('dev.advance.payment','loan_id', string='Advance Payment')
    count_installment = fields.Integer('Count Installment', compute='_get_count_installment')
    color = fields.Integer(string='Color')
    domain_loan_type_ids = fields.Many2many('dev.loan.type', string="Available Loan Types", compute="_compute_domain_loan_type_ids")
    processing_fee = fields.Boolean(string="Processing Fees")
    fee_type = fields.Selection(string="Fees Type",selection=[('fixed','Fixed'),('percentage','Percentage')],default='fixed')
    processing_fixed_amount = fields.Monetary('Fixed Amount')
    processing_percentage = fields.Float('Percentage')
    invoice_count = fields.Integer(
        'Invoice Count', compute='_compute_processing_invoice_count')
    penalty_invoice_count = fields.Integer(
        'Invoice Count', compute='_compute_penalty_invoice_count')
    witness_ids=fields.One2many('ln.witness','loan_id',string='Witness')
    checklist_line_ids = fields.One2many('checklist.line','loan_id',string="Checklist Line")
    percentage = fields.Integer(compute = 'compute_percentage')
    loan_checklist_template_id = fields.Many2one('loan.checklist.template', string='Checklist', copy=False)
    
    co_borrower=fields.Boolean(string='Co-Borrower')
    co_borrower_ids=fields.One2many('ln.co.borrower','loan_id',string='Co-Borrower')
    co_borrower_document_ids = fields.One2many(
        'ir.attachment',
        'res_id',
        string='Co-Borrower Document',
        domain=[('document_type','=','co_borrower')],
        context={
            'default_res_model': 'dev.loan.loan',
            'default_res_id': lambda self: self.id,  # Ensures attachments link to the current record
            'default_document_type': 'co_borrower', 
        }
    )
    loan_agreement = fields.Integer(string='Agreement ',compute='compute_loan_agreement_count')
    
    loan_type_color = fields.Char(string="Loan Type Color", related='loan_type_id.color')
    next_installment_date = fields.Date(string="Next Installment Date",compute="_compute_next_installment_date")
    lead_id = fields.Many2one('crm.lead',string="Lead")
    task_count = fields.Integer(compute="get_task_count")
    loan_notice=fields.Integer(string='Notice',compute='compute_loan_notice_count')

    installment_limit_type = fields.Selection(selection=[('week', 'Week'),
                                                         ('month', 'Month'),
                                                         ('year', 'Year'),
                                                         ], string='Installment Term', required=True, default='month')
    installment_type = fields.Selection(selection=[('daily', 'Day'),
                                                   ('weekly', 'Week'),
                                                   ('monthly', 'Month'),
                                                   ('quarterly', 'Quarter'),
                                                   ('semiannual', 'Semiannual'),
                                                   ('annual', 'Annual'),
                                                   ], string='Installment Type', default='monthly')
    instalment_duration = fields.Integer(string='Installment Every')
    installment_limit = fields.Integer(string='Loan Duration')

    installment_change_ids = fields.One2many(
        'loan.installment.changes', 'loan_id', string='Installment Changes')

    grace_days_for_penalty = fields.Integer("Grace Days for Penalty")
    grace_period_in_interest = fields.Integer("Grace Period")
    grace_period_for = fields.Selection(
        [('principal_amount', 'Principal Amount'), ('both', 'Principal Amount and Interest')],
        string='Grace Period For', default="principal_amount")
    installment_start_date = fields.Date('Installment Start Date', copy=False, default=fields.Date.today(),
                                         required=True)
    interest_deduction_type = fields.Selection([
        ('standard', 'Standard'),
        ('upfront', 'Upfront Interest Deduction'),
        ('upfront_with_tds', 'Upfront Interest & TDS Deduction')
    ], string='Interest Deduction Type', default='standard')
    tds_rate = fields.Float('TDS Rate (%)')
    upfront_interest_amount = fields.Monetary('Upfront Interest', compute='_compute_upfront_amounts')
    upfront_tds_amount = fields.Monetary('Upfront TDS', compute='_compute_upfront_amounts')
    net_disbursement_amount = fields.Monetary('Net Disbursement', compute='_compute_upfront_amounts')

    @api.onchange('installment_start_date')
    def onchange_installment_start_date(self):
        if self.disbursement_date and self.installment_start_date:
            if self.installment_start_date < self.disbursement_date:
                raise ValidationError(_("Installment start date must be greater than the disbursement date."))

    @api.depends('loan_amount', 'interest_rate', 'interest_deduction_type', 'tds_rate', 'installment_limit_type', 'installment_limit')
    def _compute_upfront_amounts(self):
        for loan in self:
            loan.upfront_interest_amount = 0.0
            loan.upfront_tds_amount = 0.0
            loan.net_disbursement_amount = loan.loan_amount
            if loan.interest_deduction_type in ['upfront', 'upfront_with_tds']:
                if loan.installment_limit_type == 'week':
                    total_months = loan.installment_limit * 7 / 30
                elif loan.installment_limit_type == 'month':
                    total_months = loan.installment_limit
                elif loan.installment_limit_type == 'year':
                    total_months = loan.installment_limit * 12
                else:
                    total_months = 0
                
                total_interest = round(loan.loan_amount * loan.interest_rate * total_months / 1200, 2)
                loan.upfront_interest_amount = total_interest
                if loan.interest_deduction_type == 'upfront_with_tds':
                    loan.upfront_tds_amount = round(total_interest * loan.tds_rate / 100, 2)
                
                loan.net_disbursement_amount = loan.loan_amount - loan.upfront_interest_amount - loan.upfront_tds_amount
    
    
    def compute_loan_notice_count(self):
       for loan in self:
            loan_ids=self.env['ln.notice'].search([('partner_id','=',self.client_id.id),('loan_id','=',self.id)])
            loan.loan_notice = len(loan_ids)  

    def view_loan_notice(self):
         loan_ids=self.env['ln.notice'].search([('partner_id','=',self.client_id.id),('loan_id','=',self.id)])
         list_id = loan_ids.ids
         action = self.env.ref('dev_loan_management.action_dev_loan_notice').sudo().read()[0]
         if len(list_id) > 1:
            action['domain'] = [('id', 'in', list_id)]
         elif len(list_id) == 1:
            action['views'] = [(self.env.ref('dev_loan_management.view_dev_loan_notice_form').id, 'form')]
            action['res_id'] = list_id[0]
         else:
            action = {'type': 'ir.actions.act_window_close'}
         return action

  
    # Task 
    def view_task_list(self):
        task_ids = self.env['project.task'].search([('loan_id', '=', self.id)])
        action = self.env["ir.actions.actions"]._for_xml_id('project.action_view_all_task')
        if len(task_ids) > 1:
            action['domain'] = [('id', 'in', task_ids.ids)]
        elif len(task_ids) == 1:
            action['views'] = [(self.env.ref('project.view_task_form2').id, 'form')]
            action['res_id'] = task_ids[0].id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

 
    def get_task_count(self):   
        for count in self:
            task_ids = self.env['project.task'].search([('loan_id', '=',count.id)])  
            count.task_count = len(task_ids)
    
    
    @api.depends('installment_ids.date', 'installment_ids.state')
    def _compute_next_installment_date(self):
        for record in self:
            # Get the current date
            current_date = fields.Date.today()
            
            # Filter installments: future date and unpaid
            future_unpaid_installments = record.installment_ids.filtered(
                lambda i: i.date and i.date > current_date and i.state == 'unpaid'
            )
            
            # Check if there are any future unpaid installments
            if future_unpaid_installments:
                # Get the earliest unpaid installment date
                next_date = min(future_unpaid_installments.mapped('date'))
                record.next_installment_date = next_date
            else:
                # No future unpaid installments
                record.next_installment_date = False
    
    #    PORTAL
    def _compute_access_url(self):
        super(dev_loan_loan, self)._compute_access_url()
        for loan in self:
            loan.access_url = '/my/loan/%s' % (loan.id)

    def _get_report_base_filename(self):
        self.ensure_one()
        return '%s %s' % (_('Loan'), self.name)
        
        
        
    def compute_loan_agreement_count(self):
       for loan in self:
            loan_ids=self.env['ln.agreement'].search([('partner_id','=',self.client_id.id),('loan_id','=',self.id)])
            loan.loan_agreement = len(loan_ids)
       
    def view_loan_agreement(self):
         loan_ids=self.env['ln.agreement'].search([('partner_id','=',self.client_id.id),('loan_id','=',self.id)])
         list_id = loan_ids.ids
         action = self.env.ref('dev_loan_management.action_dev_loan_agreement').sudo().read()[0]
         if len(list_id) > 1:
            action['domain'] = [('id', 'in', list_id)]
         elif len(list_id) == 1:
            action['views'] = [(self.env.ref('dev_loan_management.view_dev_loan_agreement_form').id, 'form')]
            action['res_id'] = list_id[0]
         else:
            action = {'type': 'ir.actions.act_window_close'}
         return action    
        
    @api.onchange('loan_checklist_template_id')
    def onchange_loan_checklist_template_id(self):
        if self.checklist_line_ids:
            self.checklist_line_ids = False
                       
        for line in self.loan_checklist_template_id.checklist_ids:                                                         
            self.checklist_line_ids = [(0,0,
                                       {'document_id':line.id or False,
                                        'document_type_id':line.document_type_id and line.document_type_id.id or False,}  
                                      )]   
    
    def compute_percentage(self):
        for record in self:
            if record.checklist_line_ids:
                total= len(record.checklist_line_ids.ids)
                completed_records = 0
                for rec in record.checklist_line_ids:
                    if rec.state == 'done':
                        complete_total= len(rec.ids)
                        completed_records += complete_total
                percentage = completed_records / total * 100
                record.percentage = percentage
            else:
                record.percentage = 0

    def action_view_processing_invoice(self):
        invoice_id = self.env['account.move'].search(
            [('loan_id', '=', self.id), ('move_type', '=', 'out_invoice'), ('invoice_type', '=', 'processing')])
        invoice_ids = invoice_id.ids
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        if len(invoice_ids) > 1:
            action['domain'] = [('id', 'in', invoice_ids)]
        elif len(invoice_ids) == 1:
            action['views'] = [
                (self.env.ref('account.view_move_form').id, 'form')]
            action['res_id'] = invoice_ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def _compute_processing_invoice_count(self):
        for invoice in self:
            invoice_ids = self.env['account.move'].search(
                [('loan_id', '=', self.id), ('move_type', '=', 'out_invoice'), ('invoice_type', '=', 'processing')])
            invoice.invoice_count = len(invoice_ids)

    def action_view_penalty_invoice(self):
        invoice_id = self.env['account.move'].search(
            [('loan_id', '=', self.id), ('move_type', '=', 'out_invoice'), ('invoice_type', '=', 'penalty')])
        invoice_ids = invoice_id.ids
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        if len(invoice_ids) > 1:
            action['domain'] = [('id', 'in', invoice_ids)]
        elif len(invoice_ids) == 1:
            action['views'] = [
                (self.env.ref('account.view_move_form').id, 'form')]
            action['res_id'] = invoice_ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def _compute_penalty_invoice_count(self):
        for invoice in self:
            invoice_ids = self.env['account.move'].search(
                [('loan_id', '=', self.id), ('move_type', '=', 'out_invoice'), ('invoice_type', '=', 'penalty')])
            invoice.penalty_invoice_count = len(invoice_ids)
          
    @api.depends('client_id')
    def _compute_domain_loan_type_ids(self):
        for record in self:
            if record.client_id and record.client_id.borrower_category_id:
                borrower_category_id = record.client_id.borrower_category_id.id
                loan_types = self.env['dev.loan.type'].search([('borrower_category_ids', 'in', [borrower_category_id])])
                record.domain_loan_type_ids = loan_types
            else:
                record.domain_loan_type_ids = self.env['dev.loan.type']
            
    def get_account(self, product_id):
        account_id = False
        if product_id:
            account_id = product_id.property_account_income_id or False
        if not account_id:
            account_id = product_id.categ_id and product_id.categ_id.property_account_income_categ_id or False
        return account_id

    def create_processing_fees_invoice(self):
        if self.fee_type == 'fixed':
            if self.processing_fixed_amount <= 0:
                raise ValidationError(
                    _('''Fixed Amount of Processing Fees is Zero or Less Then Zero, Invoice can't be generated !'''))
            loan_type_action = self.env.ref(
                'dev_loan_management.action_dev_loan_type')
            if not self.loan_type_id.processing_fees_product_id:
                msg = _('Configure Processing Fees Product into the Loan Type !')
                raise RedirectWarning(
                    msg, loan_type_action.id, _('Go to the Loan Type page'))

            processing_fees_product_id = self.loan_type_id and self.loan_type_id.processing_fees_product_id or False
            invoice_lines = []
            if self.loan_type_id.processing_fees_product_id:
                account_id = self.get_account(processing_fees_product_id)
                if not account_id:
                    raise ValidationError(_('''There is no income account defined for the product '%s' ''') % (
                        processing_fees_product_id.name))
                line_vals = {'product_id': processing_fees_product_id.id,
                             'name': self.name + ' : ' + 'Processing Fee',
                             'account_id': account_id.id,
                             'price_unit': self.processing_fixed_amount,
                             'quantity': 1,
                             'product_uom_id': processing_fees_product_id.uom_id and processing_fees_product_id.uom_id.id or False
                             }
                invoice_lines.append((0, 0, line_vals))

            vals = {'move_type': 'out_invoice',
                    'partner_id': self.client_id and self.client_id.id or False,
                    'loan_id': self.id,
                    'invoice_date': date.today(),
                    'invoice_type': 'processing',
                    'invoice_line_ids': invoice_lines}
            self.env['account.move'].create(vals)

        if self.fee_type == 'percentage':
            if self.processing_percentage <= 0:
                raise ValidationError(
                    _('''Percentage of Processing Fees is Zero or Less Then Zero, Invoice can't be generated !'''))
            loan_type_action = self.env.ref(
                'dev_loan_management.action_dev_loan_type')
            if not self.loan_type_id.processing_fees_product_id:
                msg = _('Configure Processing Fees Product into the Loan Type !')
                raise RedirectWarning(
                    msg, loan_type_action.id, _('Go to the Loan Type page'))

            processing_fees_product_id = self.loan_type_id and self.loan_type_id.processing_fees_product_id or False
            invoice_lines = []
            if self.loan_type_id.processing_fees_product_id:
                account_id = self.get_account(processing_fees_product_id)
                if not account_id:
                    raise ValidationError(_('''There is no income account defined for the product '%s' ''') % (
                        processing_fees_product_id.name))
                amount = 0
                if self.processing_percentage:
                    amount = (self.loan_amount *
                              self.processing_percentage / 100)
                line_vals = {'product_id': processing_fees_product_id.id,
                             'name': self.name + ' : ' + 'Processing Fee',
                             'account_id': account_id.id,
                             'price_unit': amount,
                             'quantity': 1,
                             'product_uom_id': processing_fees_product_id.uom_id and processing_fees_product_id.uom_id.id or False
                             }
                invoice_lines.append((0, 0, line_vals))

            vals = {'move_type': 'out_invoice',
                    'partner_id': self.client_id and self.client_id.id or False,
                    'loan_id': self.id,
                    'invoice_date': date.today(),
                    'invoice_type': 'processing',
                    'invoice_line_ids': invoice_lines}
            self.env['account.move'].create(vals)
        
    
    
    # def _compute_attachment_number(self):
    #     for loan in self:
    #         loan.attachment_number = len(loan.loan_document_ids.ids + loan.co_borrower_document_ids.ids)
    
    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group(
            [('res_model', '=', 'dev.loan.loan'), ('res_id', 'in', self.ids)],
            ['res_id'], ['res_id']
        )
        mapped_data = {data['res_id']: data['res_id_count'] for data in attachment_data}
        for loan in self:
            loan.attachment_number = mapped_data.get(loan.id, 0)
    
    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'dev.loan.loan'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'dev.loan.loan', 'default_res_id': self.id}
        return res
        
    def action_view_installment(self):
        if self.installment_ids:
            action = self.env.ref('dev_loan_management.action_dev_loan_installment').read()[0]
            action['domain'] = [('id', 'in', self.installment_ids.ids),('state','not in',['draft','reject','cancel'])]
            action['context']= {}
            return action
        else:
            return {'type': 'ir.actions.act_window_close'}
            
            
    def unlink(self):
        for loan in self:
            if loan.state not in ['draft','cancel']:
                raise ValidationError(_('Loan delete on Draft and cancel state only !!!.'))
        return super(dev_loan_loan, self).unlink()
        
    
    @api.depends('installment_ids')
    def _get_count_installment(self):
        for loan in self:
            if loan.installment_ids:
                loan.count_installment = len(loan.installment_ids)
            else:
                loan.count_installment = 0
                
                
    
    @api.depends('interest_rate','loan_term','loan_amount')
    def _estimated_monthly_payment(self):
        for loan in self:
            loan.emi_estimate = 0.0
            if loan.interest_rate and loan.loan_amount and loan.loan_term:
                if loan.interest_mode == 'reducing':
                    if loan.interest_rate and loan.loan_term and loan.loan_amount:
                        k = 12
                        i = loan.interest_rate / 100
                        a = i / k or 0.00
                        b = (1 - (1 / ((1 + (i / k)) ** loan.loan_term))) or 0.00
                        emi = ((loan.loan_amount * a) / b) or 0.00
                        loan.emi_estimate =  emi
                else:
                    loan.emi_estimate = (loan.loan_amount / loan.loan_term) + ((loan.loan_amount * (loan.interest_rate / 100)) / 12)
                    
                    
    def _make_url(self,model='dev.loan.loan'):
        url = self.env['ir.config_parameter'].sudo()
        base_url = url.get_param('web.base.url')
        menu_id = self.env.ref('dev_loan_management.menu_dev_loan_request_approve').id
        action_id = self.env.ref('dev_loan_management.action_dev_loan_loan_approve').id
        if base_url:
            base_url += '/web#id=%s&cids=1&menu_id=%s&action=%s&model=%s&view_type=form' % (self.id, menu_id,action_id, model)
        return base_url


    def _make_url_reject(self):
        ir_param = self.env['ir.config_parameter'].sudo()
        base_url = ir_param.get_param('web.base.url')
        menu_id = self.env.ref('dev_loan_management.menu_dev_loan_request_rejected').id
        action_id = self.env.ref('dev_loan_management.action_dev_loan_loan_rejected').id
        if base_url:
            base_url += '/web#id=%s&cids=1&menu_id=%s&action=%s&model=%s&view_type=form' % (self.id, menu_id, action_id, self._name)
        return base_url

                    
                    
    @api.depends('installment_ids')
    def get_total_interest(self):
        for loan in self:
            total_interest = 0
            paid_amount = 0
            remaing_amount = 0
            
            for adv in loan.adv_payment_lines:
                paid_amount += adv.paid_amount
                
            for installment in loan.installment_ids:
                if not getattr(installment, 'is_tds_line', False):
                    total_interest += installment.interest
                if installment.state == 'paid':
                    paid_amount+= installment.total_amount
                else:
                    remaing_amount += installment.total_amount
            loan.total_interest = total_interest
            loan.paid_amount = paid_amount
            loan.remaing_amount = remaing_amount
            
    @api.depends('installment_ids')
    def get_total_estimated_paid_amount(self):
        for loan in self:
            total_amount = 0   
            for installment in loan.installment_ids:
                if not installment.is_upfront_line:
                    total_amount += installment.total_amount
            loan.total_estimated_paid_amount = total_amount
            
    
    @api.depends('total_interest','loan_amount')
    def get_total_amount_to_pay(self):
        for loan in self:
            loan.total_amount_to_pay = loan.total_interest + loan.loan_amount
    
    def get_loan_account_journal(self):
        interest_account_id = installment_account_id = loan_payment_journal_id = False
        if not self.loan_type_id:
            raise ValidationError(_("Please Select the Loan Type !!!"))
        if self.loan_type_id.interest_account_id:
            interest_account_id = self.loan_type_id.interest_account_id and self.loan_type_id.interest_account_id.id or False
        
        if self.loan_type_id.installment_account_id:
            installment_account_id = self.loan_type_id.installment_account_id and self.loan_type_id.installment_account_id.id or False
        
        if self.loan_type_id.loan_payment_journal_id:
            loan_payment_journal_id = self.loan_type_id.loan_payment_journal_id and self.loan_type_id.loan_payment_journal_id.id or False
            
        return interest_account_id,installment_account_id,loan_payment_journal_id

    def compute_installment(self):
        if self.installment_ids:
            for installment in self.installment_ids:
                installment.with_context({'force_delete': True}).unlink()

        next_date = self.installment_start_date

        if not self.instalment_duration or self.instalment_duration <= 0:
            raise ValidationError(_('Installment Duration must be positive'))

        if not self.installment_limit or self.installment_limit <= 0:
            raise ValidationError(_('Installment Limit must be provided and greater than zero'))

        # Determine total loan period in months
        if self.installment_limit_type == 'week':
            total_months = self.installment_limit * 7 / 30
        elif self.installment_limit_type == 'month':
            total_months = self.installment_limit
        elif self.installment_limit_type == 'year':
            total_months = self.installment_limit * 12
        else:
            raise ValidationError(_('Invalid Installment Limit Type'))

        # Determine frequency interval and total installments
        if self.installment_type == 'daily':
            interval = timedelta(days=self.instalment_duration)
            total_days = total_months * 30
            total_installments = int(total_days // self.instalment_duration)
        elif self.installment_type == 'weekly':
            interval = timedelta(weeks=self.instalment_duration)
            total_days = total_months * 30
            total_installments = int(total_days // (7 * self.instalment_duration))
        elif self.installment_type == 'monthly':
            interval = relativedelta(months=self.instalment_duration)
            total_installments = int(total_months // self.instalment_duration)
        elif self.installment_type == 'quarterly':
            interval = relativedelta(months=self.instalment_duration * 3)
            total_installments = int(total_months // (self.instalment_duration * 3))
        elif self.installment_type == 'semiannual':
            interval = relativedelta(months=self.instalment_duration * 6)
            total_installments = int(total_months // (self.instalment_duration * 6))
        elif self.installment_type == 'annual':
            interval = relativedelta(years=self.instalment_duration)
            total_installments = int(total_months // (self.instalment_duration * 12))
        else:
            raise ValidationError(_('Invalid Installment Type'))

        if total_installments <= 0:
            raise ValidationError(_('Installment configuration resulted in zero installments'))

        interest_account_id, installment_account_id, loan_payment_journal_id = self.get_loan_account_journal()
        
        installment_data = []
        upfront_interest = 0.0
        upfront_tds = 0.0
        
        if self.interest_deduction_type in ['upfront', 'upfront_with_tds']:
            upfront_interest = round(self.loan_amount * (self.interest_rate or 0.0) * total_months / 1200, 2)
            if self.interest_deduction_type == 'upfront_with_tds':
                upfront_tds = round(upfront_interest * self.tds_rate / 100, 2)
            else:
                upfront_tds = 0.0
            
            # Interest Deduction Line
            if upfront_interest > 0:
                installment_data.append((0, 0, {
                    'name': f'Interest Deduction - {self.name}',
                    'client_id': self.client_id.id if self.client_id else False,
                    'date': self.disbursement_date or date.today(),
                    'opening_balance': self.loan_amount,
                    'amount': 0.0,
                    'interest': upfront_interest,
                    'closing_balance': self.loan_amount,
                    'total_amount': upfront_interest,
                    'state': 'paid',
                    'is_upfront_line': True,
                    'interest_account_id': interest_account_id or False,
                    'installment_account_id': installment_account_id or False,
                    'loan_payment_journal_id': loan_payment_journal_id or False,
                    'currency_id': self.currency_id.id if self.currency_id else False,
                }))
            
            # TDS Deduction Line
            if upfront_tds > 0:
                installment_data.append((0, 0, {
                    'name': f'TDS Deduction - {self.name}',
                    'client_id': self.client_id.id if self.client_id else False,
                    'date': self.disbursement_date or date.today(),
                    'opening_balance': self.loan_amount,
                    'amount': 0.0,
                    'interest': upfront_tds,
                    'closing_balance': self.loan_amount,
                    'total_amount': upfront_tds,
                    'state': 'paid',
                    'is_upfront_line': True,
                    'is_tds_line': True,  # Added flag to identify TDS specifically
                    'interest_account_id': interest_account_id or False,
                    'installment_account_id': installment_account_id or False,
                    'loan_payment_journal_id': loan_payment_journal_id or False,
                    'currency_id': self.currency_id.id if self.currency_id else False,
                }))

        # Principal recovery is always the full loan amount in this logic
        principal_basis = self.loan_amount
        principal_remaining = principal_basis

        # Calculate interest
        annual_interest = self.interest_rate or 0.0
        interest_list = []
        if self.interest_deduction_type != 'standard':
            interest_list = [0.0] * total_installments
        elif self.interest_mode == 'flat':
            total_interest = round(self.loan_amount * annual_interest * total_months / 1200, 2)
            raw_interest = total_interest / total_installments
            interest_list = [round(raw_interest, 2) for _ in range(total_installments - 1)]
            interest_list.append(round(total_interest - sum(interest_list), 2))
        elif self.interest_mode == 'reducing':
            if self.installment_type == 'daily':
                period_interest = annual_interest / 365
            elif self.installment_type == 'weekly':
                period_interest = annual_interest / 52
            elif self.installment_type == 'monthly':
                period_interest = annual_interest / 12
            elif self.installment_type == 'quarterly':
                period_interest = annual_interest / 4
            elif self.installment_type == 'semiannual':
                period_interest = annual_interest / 2
            elif self.installment_type == 'annual':
                period_interest = annual_interest
            else:
                period_interest = 0.0
        else:
            interest_list = [0.0] * total_installments

        # installment_data is already initialized and populated with deductions if any


        grace_installments = int(self.grace_period_in_interest or 0)
        grace_for = self.grace_period_for  # 'principal_amount' or 'both'

        if grace_installments >= total_installments:
            raise ValidationError(_("Grace period covers all installments. Please adjust values."))

        principal_installments = total_installments - (
            grace_installments if grace_for in ['principal_amount', 'both'] else 0)
        base_principal = round(principal_basis / principal_installments, 2) if principal_installments else 0

        for i in range(total_installments):
            opening_balance = principal_remaining

            # Determine principal
            if grace_installments > 0 and i < grace_installments and grace_for in ['principal_amount', 'both']:
                principal = 0.0
            elif i == total_installments - 1:
                principal = round(opening_balance, 2)
            else:
                principal = base_principal

            # Determine interest
            if self.interest_mode == 'flat':
                if grace_installments > 0 and i < grace_installments and grace_for == 'both':
                    interest = 0.0
                else:
                    interest = interest_list[i]
            elif self.interest_mode == 'reducing':
                if grace_installments > 0 and i < grace_installments and grace_for == 'both':
                    interest = 0.0
                else:
                    if i == 0 and self.installment_start_date and self.disbursement_date:
                        if self.installment_start_date >= self.disbursement_date:
                            days_gap = (self.installment_start_date - self.disbursement_date).days
                            interest = round((opening_balance * annual_interest * days_gap) / 36000, 2)
                        else:
                            interest = round((opening_balance * period_interest) / 100, 2)
                    else:
                        interest = round((opening_balance * period_interest) / 100, 2)
            else:
                interest = 0.0

            closing_balance = round(opening_balance - principal, 2)
            total_amount = float("{:.2f}".format(principal + interest))

            installment_data.append((0, 0, {
                'name': f'INS - {self.name} - {i + 1}',
                'client_id': self.client_id.id if self.client_id else False,
                'date': next_date,
                'opening_balance': opening_balance,
                'amount': principal,
                'none_interest': 0.0,
                'interest': interest,
                'closing_balance': closing_balance,
                'total_amount': total_amount,
                'state': 'unpaid',
                'interest_account_id': interest_account_id or False,
                'installment_account_id': installment_account_id or False,
                'loan_payment_journal_id': loan_payment_journal_id or False,
                'currency_id': self.currency_id.id if self.currency_id else False,
            }))

            principal_remaining = closing_balance
            next_date += interval

        self.installment_ids = installment_data
            
            
    @api.constrains('client_id','request_date')
    def check_number_of_client_loan(self):
        for loan in self:
            if loan.client_id and loan.request_date:
                no_of_loan_allow = loan.client_id.loan_request
                start_date = date(date.today().year, 1, 1)
                start_date = start_date.strftime('%Y-%m-%d')
                end_date = date(date.today().year, 12, 31)
                end_date = end_date.strftime('%Y-%m-%d')
                loan_ids = loan.env['dev.loan.loan'].search([('request_date','<=',end_date),('request_date','>=',start_date),('state','not in',['cancel','reject']),('client_id','=',loan.client_id.id)])
                
                if len(loan_ids) > no_of_loan_allow:
                    raise ValidationError(_("This Borrower allow only %s Loan Request in Year !!!")%(no_of_loan_allow))

    @api.onchange('loan_type_id')
    def onchange_loan_type(self):
        if self.loan_type_id:
            self.interest_mode = self.loan_type_id and self.loan_type_id.interest_mode or False
            self.interest_rate = self.loan_type_id and self.loan_type_id.rate or 0.0
            self.none_interest_month = self.loan_type_id and self.loan_type_id.none_interest_month or 0
            self.grace_days_for_penalty = self.loan_type_id and self.loan_type_id.grace_days_for_penalty or 0.0
            self.grace_period_in_interest = self.loan_type_id and self.loan_type_id.grace_period_in_interest or 0.0
            self.grace_period_for = self.loan_type_id and self.loan_type_id.grace_period_for or False
            self.interest_deduction_type = self.loan_type_id and self.loan_type_id.interest_deduction_type or 'standard'
            self.tds_rate = self.loan_type_id and self.loan_type_id.tds_rate or 0.0
        else:
            self.interest_rate = 0.0
            self.none_interest_month = 0

        if self.loan_type_id and self.loan_type_id.proof_ids:
            self.proof_ids = [(6, 0, self.loan_type_id.proof_ids.ids)]
        else:
            self.proof_ids = False

        if self.loan_type_id:
            self.loan_term = self.loan_type_id.loan_term_by_month
            
            
    
    @api.constrains('loan_term','loan_amount','loan_type_id')        
    def check_rate(self):
        # if self.loan_term <= 0:
        #     raise ValidationError(_("Loan Term Must be Positive !!!"))
                
        if self.loan_amount <= 0:
            raise ValidationError(_("Loan Amount Must be Positive !!!"))
                
        # if self.loan_type_id:
        #     if self.loan_term > self.loan_type_id.loan_term_by_month:
        #         raise ValidationError(_("Loan Term Must be less then or equal %s Month")%(self.loan_type_id.loan_term_by_month))
        
        if self.loan_type_id and self.loan_amount:
            if self.loan_amount > self.loan_type_id.loan_amount:
                raise ValidationError(_("Loan Amount Must be less then or equal %s Amount")%(self.loan_type_id.loan_amount))
            
        
    @api.model
    def create(self, vals):
        # Assign sequence number only if it passes validation
        loan = super(dev_loan_loan, self).create(vals)
        if loan.name == '/':  # Check if sequence number is not yet assigned
            loan.name = self.env['ir.sequence'].next_by_code('dev.loan.loan') or '/'
        return loan
    
    
    def get_loan_manager_mail(self):
        group_id = self.env.ref('dev_loan_management.group_loan_manager').id
        group_id = self.env['res.groups'].browse(group_id)
        email=''
        if group_id:
            for user in group_id.user_ids:
                if user.partner_id and user.partner_id.email:
                    if email:
                        email = email+','+ user.partner_id.email
                    else:
                        email= user.partner_id.email
        return email
        
        
    def action_confirm_loan(self):
        self.compute_installment()
        ir_model_data = self.env['ir.model.data']
        template_id = ir_model_data._xmlid_lookup('dev_loan_management.dev_loan_loan_request')[1]
        mtp = self.env['mail.template']
        template_id = mtp.browse(template_id)
        email = self.get_loan_manager_mail()
        template_id.write({'email_to': email})
        template_id.send_mail(self.ids[0], True)
        if self.loan_type_id and self.loan_type_id.is_required_documents:
            if self.percentage != 100.0:
                raise ValidationError(_("not submitted 100% Document so please submit "))
        self.state = 'confirm'
    
    def action_approve_loan(self):
        self.state = 'approve'
        if self.loan_type_id:
            self.loan_account_id = self.loan_type_id.loan_account_id and self.loan_type_id.loan_account_id.id or False
            self.disburse_journal_id = self.loan_type_id.disburse_journal_id and self.loan_type_id.disburse_journal_id.id or False
        self.approve_date = date.today()
        
    def action_set_to_draft(self):
        if self.installment_ids:
            for installment in self.installment_ids:
                installment.unlink()
        self.state = 'draft'
    
    
    
    def get_account_move_vals(self):
        if not self.disburse_journal_id:
            raise ValidationError(_("Select Disburse Journal !!!"))
        vals={
            'date':self.disbursement_date,
            'ref':self.name or 'Loan Disburse',
            'journal_id':self.disburse_journal_id and self.disburse_journal_id.id or False,
            'company_id':self.company_id and self.company_id.id or False,
        }
        return vals
    
    
    def get_credit_lines(self):
        if not self.loan_account_id:
            raise ValidationError(_("Select Disburse Account !!!"))
        
        credit_amount = self.loan_amount
        if self.interest_deduction_type != 'standard':
            credit_amount = self.net_disbursement_amount
            
        vals={
            'partner_id':self.client_id and self.client_id.id or False,
            'account_id':self.loan_account_id and self.loan_account_id.id or False,
            'credit':credit_amount,
            'name':self.name or '/',
            'date_maturity':self.disbursement_date,
        }
        return vals
    
    def get_interest_deduction_lines(self):
        interest_account_id = self.loan_type_id and self.loan_type_id.interest_account_id and self.loan_type_id.interest_account_id.id or False
        if not interest_account_id:
            raise ValidationError(_("Configure Interest Account in Loan Type !!!"))
        vals = {
            'partner_id': self.client_id and self.client_id.id or False,
            'account_id': interest_account_id,
            'credit': self.upfront_interest_amount,
            'name': f'Upfront Interest Deduction - {self.name}',
            'date_maturity': self.disbursement_date,
        }
        return vals

    def get_tds_deduction_lines(self):
        tds_account_id = self.loan_type_id and self.loan_type_id.tds_account_id and self.loan_type_id.tds_account_id.id or False
        if not tds_account_id:
            raise ValidationError(_("Configure TDS Account in Loan Type !!!"))
        vals = {
            'partner_id': self.client_id and self.client_id.id or False,
            'account_id': tds_account_id,
            'credit': self.upfront_tds_amount,
            'name': f'Upfront TDS Deduction - {self.name}',
            'date_maturity': self.disbursement_date,
        }
        return vals
    
    def get_debit_lines(self):
        if self.client_id and not self.client_id.property_account_receivable_id:
            raise ValidationError(_("Select Client Receivable Account !!!"))
        
        debit_amount = self.loan_amount
        if self.interest_deduction_type != 'standard':
            debit_amount = self.loan_amount + self.upfront_interest_amount
            
        vals={
            'partner_id':self.client_id and self.client_id.id or False,
            'account_id':self.client_id.property_account_receivable_id and self.client_id.property_account_receivable_id.id or False,
            'debit':debit_amount,
            'name':self.name or '/',
            'date_maturity':self.disbursement_date,
        }
        return vals

    def action_disburse_loan(self):
        self.disbursement_date = date.today()

        if self.disbursement_date and self.installment_start_date:
            if self.installment_start_date < self.disbursement_date:
                raise ValidationError(_(
                    "Installment start date (%s) must be greater than the disbursement date (%s)."
                ) % (
                      format_date(self.env, self.installment_start_date),
                      format_date(self.env, self.disbursement_date)
                  ))

        if self.disbursement_date:
            # 1. Main Disbursement Entry (Balanced: Net Cash)
            account_move_val = self.get_account_move_vals()
            main_move = self.env['account.move'].create(account_move_val)
            
            # Debit Receivable (Net Disbursement Amount)
            debit_line = self.get_debit_lines()
            debit_line.update({'debit': self.net_disbursement_amount, 'credit': 0})
            # Credit Bank (Net Disbursement Amount)
            credit_line = self.get_credit_lines()
            credit_line.update({'debit': 0, 'credit': self.net_disbursement_amount})
            
            main_move.line_ids = [(0, 0, debit_line), (0, 0, credit_line)]
            main_move.action_post()
            self.disburse_journal_entry_id = main_move.id
            
            # 2. Separate Interest Entry (Balanced: Interest only)
            interest_move = False
            if self.upfront_interest_amount > 0:
                interest_move = self.env['account.move'].create(self.get_account_move_vals())
                # Credit Interest Income
                credit_int = self.get_interest_deduction_lines()
                # Debit Receivable
                debit_int = self.get_debit_lines()
                debit_int.update({
                    'debit': self.upfront_interest_amount,
                    'credit': 0,
                    'name': f'Upfront Interest - {self.name}'
                })
                interest_move.line_ids = [(0, 0, credit_int), (0, 0, debit_int)]
                interest_move.action_post()

            # 3. Separate TDS Entry (Balanced: TDS only)
            tds_move = False
            if self.interest_deduction_type == 'upfront_with_tds' and self.upfront_tds_amount > 0:
                tds_move = self.env['account.move'].create(self.get_account_move_vals())
                # Credit TDS Liability
                credit_tds = self.get_tds_deduction_lines()
                # Debit Receivable
                debit_tds = self.get_debit_lines()
                debit_tds.update({
                    'debit': self.upfront_tds_amount,
                    'credit': 0,
                    'name': f'Upfront TDS - {self.name}'
                })
                tds_move.line_ids = [(0, 0, credit_tds), (0, 0, debit_tds)]
                tds_move.action_post()

        if self.disburse_journal_entry_id:
            self.state = 'disburse'
            self.compute_installment()
            
            # Link installments to their specific entries
            for installment in self.installment_ids:
                if installment.is_upfront_line:
                    if installment.is_tds_line and tds_move:
                        installment.write({'journal_entry_id': tds_move.id, 'payment_date': self.disbursement_date})
                    elif not installment.is_tds_line and interest_move:
                        installment.write({'journal_entry_id': interest_move.id, 'payment_date': self.disbursement_date})
                else:
                    # Regular installments can be linked to the main move or left for later payment
                    pass
        
    
    
    def action_open_loan(self):
        self.state = 'open'
        
    
    def action_cancel(self):
        self.state = 'cancel'

        


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
