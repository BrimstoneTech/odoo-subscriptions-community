from odoo import models, fields, api, _
from datetime import timedelta

class SubscriptionLine(models.Model):
    _name = 'flexirenew.subscription_line'
    _description = 'Subscription Line Item'

    subscription_id = fields.Many2one('flexirenew.subscription', string='Subscription', ondelete='cascade', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    name = fields.Char(string='Description', required=True)
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    price_unit = fields.Monetary(string='Price', currency_field='currency_id', required=True)
    discount = fields.Float(string='Discount (%)', default=0.0)
    
    currency_id = fields.Many2one(related='subscription_id.currency_id', string='Currency', readonly=True)
    
    price_subtotal = fields.Monetary(string='Subtotal', compute='_compute_amount', store=True, currency_field='currency_id')

    @api.depends('quantity', 'price_unit', 'discount')
    def _compute_amount(self):
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            line.price_subtotal = line.quantity * price

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.get_product_multiline_description_sale()
            self.price_unit = self.product_id.lst_price

class FlexiRenewSubscription(models.Model):
    _name = 'flexirenew.subscription'
    _description = 'Subscription & Renewal Manager'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Subscription Name', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True, tracking=True)
    type = fields.Selection([
        ('incoming', 'Incoming (Client)'),
        ('outgoing', 'Outgoing (Business Cost)')
    ], string='Direction', default='incoming', required=True, tracking=True)
    
    line_ids = fields.One2many('flexirenew.subscription_line', 'subscription_id', string='Subscription Lines')
    amount = fields.Monetary(string='Renewal Amount', compute='_compute_amount', store=True, tracking=True)
    
    mrr = fields.Monetary(string='Monthly Recurring Revenue (MRR)', compute='_compute_recurring_revenue', store=True)
    arr = fields.Monetary(string='Annual Recurring Revenue (ARR)', compute='_compute_recurring_revenue', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    start_date = fields.Date(string='Start Date', default=fields.Date.today)
    next_renewal_date = fields.Date(string='Next Renewal Date', required=True, tracking=True)
    
    frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom Days')
    ], string='Recurrence', default='monthly', required=True)
    
    custom_days = fields.Integer(string='Days to Auto-Renew', default=30)
    
    reminder_days_before = fields.Integer(string='Remind X Days Before', default=7, help="Simple 'Days before' alert.")
    reminder_enabled = fields.Boolean(string='Enable Automated Reminders', default=True)

    prorate_first_period = fields.Boolean(string='Prorate First Period', default=False,
                                          help="If checked, the first invoice will be calculated based on the days remaining in the cycle.")

    auto_generate_document = fields.Boolean(string='Auto-Generate Document', default=False, 
                                          help="Creates a Draft Invoice (Incoming) or Draft Bill (Outgoing) on renewal.")
    auto_post_and_send = fields.Boolean(string='Auto-Post & Send', default=False,
                                       help="If enabled, the system will automatically validate the invoice and email it to the partner.")
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('suspended', 'Suspended'),
        ('renewed', 'Renewed'),
        ('expired', 'Expired'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    notes = fields.Text(string='Notes')

    @api.depends('line_ids.price_subtotal')
    def _compute_amount(self):
        for rec in self:
            rec.amount = sum(rec.line_ids.mapped('price_subtotal'))

    @api.depends('amount', 'frequency', 'custom_days', 'state', 'type')
    def _compute_recurring_revenue(self):
        for rec in self:
            if rec.state != 'active' or rec.type != 'incoming':
                rec.mrr = 0.0
                rec.arr = 0.0
                continue
            
            # Simple MRR/ARR logic
            if rec.frequency == 'monthly':
                rec.mrr = rec.amount
                rec.arr = rec.amount * 12
            elif rec.frequency == 'yearly':
                rec.mrr = rec.amount / 12
                rec.arr = rec.amount
            elif rec.frequency == 'custom' and rec.custom_days:
                rec.mrr = (rec.amount / rec.custom_days) * 30
                rec.arr = (rec.amount / rec.custom_days) * 365
            else:
                rec.mrr = 0.0
                rec.arr = 0.0

    def action_activate(self):
        self.write({'state': 'active'})

    def action_pause(self):
        self.write({'state': 'suspended'})

    def action_resume(self):
        self.write({'state': 'active'})

    def action_renew(self):
        """ Manually trigger the renewal cycle """
        for rec in self:
            # 1. Create Document if enabled
            move = False
            if rec.auto_generate_document:
                move = rec._create_renewal_document()
            
            # 2. Automation: Post & Send
            if move and rec.auto_post_and_send and rec.type == 'incoming':
                move.action_post()
                rec._send_invoice_to_partner(move)
            
            # 3. Update Dates
            new_date = rec._calculate_next_date(rec.next_renewal_date)
            rec.write({
                'next_renewal_date': new_date,
                'state': 'active'
            })
            
            # 4. Log
            rec.message_post(body=_("Subscription successfully renewed. Next date: %s") % new_date)

    def _send_invoice_to_partner(self, move):
        template = self.env.ref('account.email_template_edi_invoice', raise_if_not_found=False)
        if template:
            move.message_post_with_template(template.id, email_layout_xmlid="mail.mail_notification_layout_with_responsible_signature")

    def _calculate_next_date(self, current_date):
        if self.frequency == 'monthly':
            return current_date + timedelta(days=30) # Simplified for now
        elif self.frequency == 'yearly':
            return current_date + timedelta(days=365)
        else:
            return current_date + timedelta(days=self.custom_days)

    def _create_renewal_document(self):
        move_type = 'out_invoice' if self.type == 'incoming' else 'in_invoice'
        
        # 1. Try finding account from Partner properties
        account = self.partner_id.property_account_receivable_id if self.type == 'incoming' else self.partner_id.property_account_payable_id
        
        # 2. Fallback to Company's default chart settings if partner's is empty
        if not account:
            account_type = 'asset_receivable' if self.type == 'incoming' else 'liability_payable'
            account = self.env['account.account'].search([
                ('account_type', '=', account_type),
                ('company_id', '=', self.company_id.id)
            ], limit=1)
        
        if not account:
            # Final safety check: This shouldn't happen on a valid Odoo setup
            return

        move = self.env['account.move'].create({
            'move_type': move_type,
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'product_id': line.product_id.id,
                'name': line.name,
                'quantity': line.quantity,
                'price_unit': self._get_line_price(line),
                'discount': line.discount,
                'account_id': account.id,
            }) for line in self.line_ids],
        })
        return move

    def _get_line_price(self, line):
        if not self.prorate_first_period or self.state != 'draft':
            return line.price_unit
        
        # Simple Proration: days left in the month
        today = fields.Date.today()
        # Find end of month
        import calendar
        _, last_day = calendar.monthrange(today.year, today.month)
        days_in_month = last_day
        days_remaining = (last_day - today.day) + 1
        
        if days_remaining < days_in_month:
            return (line.price_unit / days_in_month) * days_remaining
        return line.price_unit

    @api.model
    def _cron_flexirenew_reminders(self):
        """ Daily check for upcoming renewals """
        today = fields.Date.today()
        subscriptions = self.search([
            ('state', '=', 'active'),
            ('reminder_enabled', '=', True)
        ])
        
        for sub in subscriptions:
            reminder_date = sub.next_renewal_date - timedelta(days=sub.reminder_days_before)
            if today == reminder_date:
                # Trigger Notification
                sub._send_renewal_alert()

    def _send_renewal_alert(self):
        template = self.env.ref('flexirenew.mail_template_renewal_alert', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)

    @api.model
    def get_dashboard_stats(self):
        """ Fetch stats for the OWL dashboard """
        subs = self.search([('state', '=', 'active'), ('type', '=', 'incoming')])
        return {
            'mrr': sum(subs.mapped('mrr')),
            'arr': sum(subs.mapped('arr')),
            'active_count': len(subs),
            'currency_symbol': self.env.company.currency_id.symbol,
        }
