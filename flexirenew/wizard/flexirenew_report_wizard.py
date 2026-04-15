from odoo import models, fields, api

class FlexiRenewReportWizard(models.TransientModel):
    _name = 'flexirenew.report.wizard'
    _description = 'Financial Report Export Wizard'

    preview_html = fields.Html(string='Preview', compute='_compute_preview', readonly=True)

    @api.depends()
    def _compute_preview(self):
        for wizard in self:
            subs = self.env['flexirenew.subscription'].search([('state', '=', 'active'), ('type', '=', 'incoming')])
            mrr = sum(sub.mrr for sub in subs)
            arr = sum(sub.arr for sub in subs)
            currency = self.env.company.currency_id.symbol

            html = f"""
            <div class="row">
                <div class="col-6">
                    <h3 class="text-primary">MRR: {currency}{mrr:,.2f}</h3>
                </div>
                <div class="col-6">
                    <h3 class="text-info">ARR: {currency}{arr:,.2f}</h3>
                </div>
            </div>
            <hr/>
            <h4>Active Subscriptions ({len(subs)})</h4>
            <table class="table table-sm table-striped">
                <thead>
                    <tr>
                        <th>Subscription</th>
                        <th>Partner</th>
                        <th class="text-end">MRR</th>
                    </tr>
                </thead>
                <tbody>
            """
            for sub in subs:
                html += f"""
                    <tr>
                        <td>{sub.name}</td>
                        <td>{sub.partner_id.name}</td>
                        <td class="text-end">{currency}{sub.mrr:,.2f}</td>
                    </tr>
                """
            html += """
                </tbody>
            </table>
            """
            wizard.preview_html = html

    def action_export_pdf(self):
        # We trigger the report associated with the active subscriptions
        subs = self.env['flexirenew.subscription'].search([('state', '=', 'active'), ('type', '=', 'incoming')])
        # We need a report action for this. Odoo reports usually take record IDs.
        # We can pass the company or wizard id to the report.
        return self.env.ref('flexirenew.action_report_financial_summary').report_action(self.id)

    def action_export_csv(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/flexirenew/export/csv',
            'target': 'self',
        }

    def action_print(self):
        # Using a special route or just triggering the report with HTML mode?
        # Actually, the action_report_financial_summary if it's set to 'qweb-html' it can be printed via JS.
        # However, for a simple implementation, returning act_url to an html report is easiest.
        report_url = f'/report/html/flexirenew.action_report_financial_summary/{self.id}'
        return {
            'type': 'ir.actions.act_url',
            'url': report_url,
            'target': 'new',
        }
