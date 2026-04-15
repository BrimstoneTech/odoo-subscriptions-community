import csv
import io
from odoo import http
from odoo.http import request

class FinancialExportController(http.Controller):

    @http.route(['/flexirenew/export/csv'], type='http', auth="user")
    def export_financial_csv(self, **kw):
        subs = request.env['flexirenew.subscription'].search([('state', '=', 'active'), ('type', '=', 'incoming')])
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(['Subscription Name', 'Customer', 'Start Date', 'Next Renewal Date', 'Frequency', 'Monthly Recurring Revenue (MRR)', 'Annual Recurring Revenue (ARR)', 'Currency'])

        # Write data
        currency = request.env.company.currency_id.name
        for sub in subs:
            writer.writerow([
                sub.name,
                sub.partner_id.name,
                str(sub.start_date) if sub.start_date else '',
                str(sub.next_renewal_date) if sub.next_renewal_date else '',
                sub.frequency,
                f"{sub.mrr:.2f}",
                f"{sub.arr:.2f}",
                currency
            ])

        output.seek(0)
        filename = "Financial_Summary.csv"
        return request.make_response(output.getvalue(),
            headers=[('Content-Type', 'text/csv'),
                     ('Content-Disposition', f'attachment; filename="{filename}"')])
