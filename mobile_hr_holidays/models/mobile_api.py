from odoo import _, api, models


class MobileApi(models.AbstractModel):
    _inherit = 'mobile.api'

    @api.model
    def _mobile_features(self):
        return super()._mobile_features() + ['timeoff']

    @api.model
    def _mobile_record_services(self):
        return dict(super()._mobile_record_services(), timeoff='mobile.timeoff.service')

    @api.model
    def _mobile_access(self):
        access = super()._mobile_access()
        user = self.env.user
        Leave = self.env['hr.leave']
        if not Leave.has_access('read'):
            return access
        employee = user.employee_id
        capabilities = {
            # Own requests need an employee record linked to the user.
            'request': bool(employee) and Leave.has_access('create'),
            'approve': user.has_group('hr_holidays.group_hr_holidays_responsible')
            or user.has_group('hr_holidays.group_hr_holidays_user'),
            'team': bool(employee),
        }
        if any(capabilities.values()):
            access['timeoff'] = capabilities
            if capabilities['approve']:
                access.setdefault('dashboard', {})['view'] = True  # the overview shows what they can manage
        return access

    @api.model
    def _mobile_list_versions(self, keys):
        versions = super()._mobile_list_versions(keys)
        if 'timeoff.dashboard' in keys and self._mobile_can('timeoff'):
            versions['timeoff.dashboard'] = self.env['mobile.timeoff.service']._mobile_dashboard_version()
        return versions

    @api.model
    def _mobile_home_tiles(self):
        return super()._mobile_home_tiles() + [
            {'key': 'timeoff', 'label': _('Time off'), 'feature': 'timeoff', 'capability': None, 'sequence': 10},
            {'key': 'timeoff_approve', 'label': _('Approve time off'), 'feature': 'timeoff', 'capability': 'approve', 'sequence': 11},
            {'key': 'timeoff_team', 'label': _('Team time off'), 'feature': 'timeoff', 'capability': 'team', 'sequence': 12},
        ]

    @api.model
    def _mobile_home_shortcuts(self):
        return super()._mobile_home_shortcuts() + [
            {'key': 'timeoff_new', 'label': _('New time off request'), 'feature': 'timeoff', 'capability': 'request'},
        ]

    @api.model
    def _mobile_home_tabs(self):
        return super()._mobile_home_tabs() + [
            {'key': 'timeoff', 'label': _('Time off'), 'feature': 'timeoff', 'capability': None, 'sequence': 40},
        ]
