# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

class SubscriptionPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super(SubscriptionPortal, self)._prepare_home_portal_values(counters)
        if 'subscription_count' in counters:
            values['subscription_count'] = request.env['flexirenew.subscription'].search_count([
                ('partner_id', '=', request.env.user.partner_id.id),
                ('state', 'in', ['active', 'past_due', 'suspended'])
            ])
        return values

    @http.route(['/my/subscriptions', '/my/subscriptions/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_subscriptions(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        Subscription = request.env['flexirenew.subscription']
        domain = [('partner_id', '=', request.env.user.partner_id.id)]

        count = Subscription.search_count(domain)
        pager = portal_pager(
            url="/my/subscriptions",
            total=count,
            page=page,
            step=self._items_per_page
        )
        subscriptions = Subscription.search(domain, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'subscriptions': subscriptions,
            'page_name': 'subscription',
            'pager': pager,
            'default_url': '/my/subscriptions',
        })
        return request.render("flexirenew.portal_my_subscriptions", values)

    @http.route(['/my/subscriptions/<int:subscription_id>'], type='http', auth="public", website=True)
    def portal_subscription_page(self, subscription_id, report_type=None, access_token=None, message=False, download=False, **kw):
        try:
            subscription_sudo = self._document_check_access('flexirenew.subscription', subscription_id, access_token)
        except Exception:
            return request.redirect('/my')

        values = {
            'subscription': subscription_sudo,
            'message': message,
            'token': access_token,
            'bootstrap_formatting': True,
            'partner_id': subscription_sudo.partner_id.id,
            'report_type': 'html',
            'page_name': 'subscription',
        }
        return request.render("flexirenew.portal_subscription_page", values)

    @http.route(['/my/subscriptions/<int:subscription_id>/cancel'], type='http', auth="user", methods=['POST'], website=True)
    def portal_subscription_cancel(self, subscription_id, **kw):
        subscription = request.env['flexirenew.subscription'].browse(subscription_id)
        if subscription.partner_id.id != request.env.user.partner_id.id:
            return request.redirect('/my')
        
        subscription.write({'state': 'cancel'})
        subscription.message_post(body=_("Subscription cancelled by customer from portal."))
        return request.redirect('/my/subscriptions/%s?message=cancelled' % subscription_id)
