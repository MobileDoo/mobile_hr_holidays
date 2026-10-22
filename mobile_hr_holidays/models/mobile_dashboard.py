from datetime import timedelta

from odoo import _, api, models


class MobileDashboardService(models.AbstractModel):
    _inherit = 'mobile.dashboard.service'

    @api.model
    def _card_defs(self):
        return super()._card_defs() + [
            {'key': 'timeoff_to_approve', 'section': 'approvals', 'feature': 'timeoff', 'capability': 'approve',
             'build': '_card_timeoff_to_approve'},
            {'key': 'timeoff_today', 'section': 'people', 'feature': 'timeoff', 'capability': 'approve',
             'build': '_card_timeoff_today'},
        ]

    @api.model
    def _card_timeoff_to_approve(self):
        service = self.env['mobile.timeoff.service']
        return self._count_card(service._mobile_model, service._mobile_scope_domain('to_approve', {}),
                                _('Time off to approve'), 'calendar-check', 'teal', tile='timeoff_approve',
                                tone_if_any='warn')

    @api.model
    def _card_timeoff_today(self):
        today = self._today()
        start = self._local_day_start_utc(today)
        end = self._local_day_start_utc(today + timedelta(days=1))
        domain = [('state', '=', 'validate'), ('date_from', '<', end), ('date_to', '>=', start)]
        return self._count_card('hr.leave', domain, _('On leave today'), 'beach', 'teal', tile='timeoff_team')
