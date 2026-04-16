{
    'name': 'Subscriptions: Ultimate Multi-Level Follow-Up & Analytics',
    'version': '1.1.0',
    'price': 294.00,
    'currency': 'USD',
    'license': 'OPL-1',
    'summary': 'Professional Service Contract Management with MRR/ARR Dashboards',
    'description': """
🎉 **LAUNCH PROMO: 30% OFF FOR THE FIRST 5 BUYERS!** 🎉
*(Regular price: $420.00. Grab it now before the price automatically goes up!)*

Subscriptions Management: The Enterprise-Grade Engine for Community
==================================================================
A high-performance standalone module that transforms Odoo into a powerful subscription recurring engine.

Key Highlights:
---------------
*   **Command Center Dashboard**: Real-time MRR/ARR analytics and growth tracking.
*   **Contract-Level Lines**: Manage complex bundles with multiple products in a single subscription.
*   **Proration Engine**: Professional billing for mid-cycle starts and changes.
*   **Auto-Post & Send**: Fully automated invoicing lifecycle.
*   **Self-Service Portal**: Customers can view, download, and cancel their own subscriptions.

Contact & Support:
------------------
Brimstone Tech
Email: brimstonetech1@gmail.com
Phone: +256 744 429 293
    """,
    'author': 'BrimstoneTech',
    'website': 'https://brimstonetech1@gmail.com',
    'support': 'brimstonetech1@gmail.com',
    'category': 'Accounting/Management',
    'depends': ['base', 'mail', 'account', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'data/mail_templates.xml',
        'data/ir_cron.xml',
        'wizard/flexirenew_report_wizard_views.xml',
        'report/financial_report_templates.xml',
        'report/financial_report.xml',
        'views/flexirenew_subscription_views.xml',
        'views/menu_views.xml',
        'views/portal_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'flexirenew/static/src/js/subscriptions_dashboard.js',
            'flexirenew/static/src/xml/subscriptions_dashboard.xml',
        ],
    },
    'installable': True,
    'application': True,
    'images': ['static/description/icon.png'],
}
