from odoo import http
from odoo.http import request

from odoo.addons.mobile_connector.controllers.utils import mobile_route, require_access


class MobileTimeoffController(http.Controller):
    """Time Off specific endpoints. Lists and forms go through `/mobile/api/v1/records/timeoff/...`."""

    @mobile_route('/mobile/api/v1/timeoff/dashboard')
    def dashboard(self, payload):
        require_access('timeoff')
        return request.env['mobile.timeoff.service']._mobile_dashboard()
