"""Time Off on mobile: configuration of the generic record service + dashboard and pushes.

Customer modules extend the mobile behaviour by `_inherit`-ing
`mobile.timeoff.service` and overriding the `_mobile_*` hooks (see
`mobile.record.service`) — never by patching the controllers.
"""
import logging

from odoo import _, api, fields, models
from odoo.tools import float_round
from odoo.tools.translate import code_translations

_logger = logging.getLogger(__name__)


class MobileTimeoffService(models.AbstractModel):
    _name = 'mobile.timeoff.service'
    _inherit = 'mobile.record.service'
    _description = 'Mobile Time Off Service'

    _mobile_model = 'hr.leave'
    _mobile_feature = 'timeoff'
    _mobile_create_capability = 'request'
    _mobile_scope_capabilities = {'mine': 'request', 'to_approve': 'approve', 'team': 'team'}
    # Missing ones (other Odoo versions) are skipped.
    _mobile_core_field_names = [
        'employee_id',
        'holiday_status_id',
        'request_date_from',
        'request_date_to',
        'request_unit_half',
        'request_date_from_period',
        'request_unit_hours',
        'request_hour_from',
        'request_hour_to',
        'name',
        'number_of_days',
        'duration_display',
        'state',
        'leave_type_request_unit',
        'leave_type_support_document',
    ]
    _mobile_list_field_names = [
        'employee_id',
        'holiday_status_id',
        'request_date_from',
        'request_date_to',
        'date_from',
        'date_to',
        'duration_display',
        'number_of_days',
        'state',
        'can_approve',
    ]

    # ------------------------------------------------------------------
    # Hooks
    # ------------------------------------------------------------------

    @api.model
    def _mobile_duration_text(self, leave):
        """"3 ngày" / "3 days" in the reader's language.

        `hr.leave.duration_display` is stored in the language of whoever created the
        request, so a manager would read the employee's language. Same format and
        words as Odoo (hr_holidays' own translations).
        """
        hours = leave.leave_type_request_unit == 'hour'
        amount = float_round(leave.number_of_hours if hours else leave.number_of_days,
                             precision_digits=2)
        word = 'hours' if hours else 'days'
        translations = code_translations.get_python_translations('hr_holidays', self.env.lang or 'en_US')
        return '%g %s' % (amount, translations.get(word, word))

    @api.model
    def _serialize(self, record, extra=None):
        values = super()._serialize(record, extra)
        if 'duration_display' in values:
            values['duration_display'] = self._mobile_duration_text(record)
        return values

    @api.model
    def _mobile_spec(self, record=None, values=None):
        spec = super()._mobile_spec(record, values)
        # Saved request: stored text; a request being edited is recomputed by onchange in the reader's language.
        if record and values is None and 'duration_display' in spec.get('values', {}):
            spec['values']['duration_display'] = self._mobile_duration_text(record)
        return spec

    @api.model
    def _mobile_new_context(self):
        employee = self.env.user.employee_id
        return {'default_employee_id': employee.id} if employee else {}

    @api.model
    def _mobile_domain(self, scope, params):
        employee = self.env.user.employee_id
        if scope == 'mine':
            return [('employee_id', '=', employee.id)] if employee else [('id', '=', 0)]
        if scope == 'to_approve':
            states = ['confirm', 'validate1']
            if self.env.user.has_group('hr_holidays.group_hr_holidays_user'):
                return [('state', 'in', states)]
            if self.env.user.has_group('hr_holidays.group_hr_holidays_responsible'):
                return [('state', 'in', states), ('employee_id.leave_manager_id', '=', self.env.uid)]
            return [('id', '=', 0)]
        if scope == 'team':
            if not employee:
                return [('id', '=', 0)]
            domain = [('state', 'in', ['confirm', 'validate1', 'validate'])]
            if employee.department_id:
                domain.append(('employee_id.department_id', '=', employee.department_id.id))
            else:
                domain.append(('employee_id.parent_id', '=', employee.parent_id.id or employee.id))
            return domain
        return super()._mobile_domain(scope, params)

    @api.model
    def _mobile_order(self, scope):
        return 'date_from asc' if scope == 'team' else 'date_from desc, id desc'

    @api.model
    def _mobile_on_state_change(self, leave, old_state, new_state):
        """Push the employee when their request is decided.

        Approvers are notified by mobile_connector's generic activity push
        (hr_holidays schedules an approval activity for the right person).
        """
        user = leave.employee_id.user_id
        if not user or user == self.env.user or new_state not in ('validate', 'refuse'):
            return
        title, body = self._mobile_push_text(leave, new_state)
        self.env['mobile.push.message']._enqueue(user, title, body, {
            'type': 'timeoff',
            'model': 'hr.leave',
            'res_id': leave.id,
            'state': new_state,
        })

    @api.model
    def _mobile_push_text(self, leave, state):
        leave = leave.with_context(lang=leave.employee_id.user_id.lang)
        period = self.with_context(lang=leave.env.lang)._mobile_duration_text(leave)
        dates = fields.Date.to_string(leave.request_date_from) if leave.request_date_from else ''
        if state == 'validate':
            return _('Time off approved'), f'{leave.holiday_status_id.name} · {dates} · {period}'
        return _('Time off refused'), f'{leave.holiday_status_id.name} · {dates} · {period}'

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------

    @api.model
    def _mobile_dashboard_version(self):
        """Balances depend on allocations too, not only on leaves."""
        api_model = self.env['mobile.api']
        parts = [self._mobile_list_version('mine'), self._mobile_list_version('to_approve')]
        employee = self.env.user.employee_id
        if employee:
            parts.append(api_model._mobile_domain_version('hr.leave.allocation', [('employee_id', '=', employee.id)]))
        return '|'.join(parts)

    @api.model
    def _mobile_dashboard(self):
        user = self.env.user
        employee = user.employee_id
        balances = []
        if employee:
            try:
                data = self.env['hr.leave.type'].with_context(
                    employee_id=employee.id,
                    allowed_company_ids=self.env.companies.ids,
                ).get_allocation_data_request()
                for name, info, requires_allocation, type_id in data:
                    balances.append({
                        'leave_type_id': type_id,
                        'name': name,
                        'requires_allocation': requires_allocation == 'yes',
                        'unit': info.get('request_unit'),
                        'max_leaves': info.get('max_leaves', 0),
                        'leaves_taken': info.get('leaves_taken', 0),
                        'leaves_requested': info.get('leaves_requested', 0),
                        'remaining_leaves': info.get('remaining_leaves', 0),
                        'virtual_remaining_leaves': info.get('virtual_remaining_leaves', 0),
                        'expire': info.get('closest_allocation_expire') or False,
                    })
            except Exception:  # never break the dashboard because of balance computation
                _logger.exception('mobile_hr_holidays: cannot compute allocation data')

        today = fields.Date.context_today(self)
        upcoming = self.env['hr.leave'].search([
            ('employee_id', '=', employee.id),
            ('state', 'in', ['confirm', 'validate1', 'validate']),
            ('date_to', '>=', fields.Datetime.to_string(fields.Datetime.now())),
        ], order='date_from asc', limit=5) if employee else self.env['hr.leave']
        to_approve = self.env['hr.leave'].search_count(self._mobile_domain('to_approve', {}))
        return {
            'employee': [employee.id, employee.name] if employee else False,
            'balances': balances,
            'upcoming': [self._serialize(leave) for leave in upcoming],
            'to_approve_count': to_approve,
            'is_officer': user.has_group('hr_holidays.group_hr_holidays_user'),
            'is_approver': user.has_group('hr_holidays.group_hr_holidays_responsible'),
            'today': fields.Date.to_string(today),
            'state_selection': self._state_selection(),
            'version': self._mobile_dashboard_version(),
        }
