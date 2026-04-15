/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Layout } from "@web/search/layout";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";

export class SubscriptionsDashboard extends Component {
    static template = "flexirenew.SubscriptionsDashboard";
    static components = { Layout };

    setup() {
        this.rpc = useService("rpc");
        this.action = useService("action");
        this.state = useState({
            stats: {
                mrr: 0,
                arr: 0,
                active_count: 0,
                currency_symbol: '$'
            }
        });

        onWillStart(async () => {
            await this.loadStats();
        });
    }

    async loadStats() {
        try {
            const stats = await this.rpc("/web/dataset/call_kw/flexirenew.subscription/get_dashboard_stats", {
                model: 'flexirenew.subscription',
                method: 'get_dashboard_stats',
                args: [],
                kwargs: {},
            });
            if (stats) {
                this.state.stats = stats;
            }
        } catch (error) {
            console.error("Dashboard Stats Load Failed:", error);
        }
    }

    openSubscriptions() {
        this.action.doAction("flexirenew.action_flexirenew_all");
    }

    openRevenue() {
        this.action.doAction("flexirenew.action_flexirenew_revenue");
    }

    exportReport() {
        this.action.doAction("flexirenew.action_flexirenew_report_wizard");
    }
}

registry.category("actions").add("subscriptions_dashboard", SubscriptionsDashboard);
