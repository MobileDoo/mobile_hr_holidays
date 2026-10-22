from odoo import api, models


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    @api.model_create_multi
    def create(self, vals_list):
        # Odoo 18 refuses a request without `employee_id` before defaults apply, and its form hides the field:
        # apply the context default first (the app passes the requester as `default_employee_id`).
        default = self.env.context.get('default_employee_id')
        if default:
            vals_list = [dict(vals, employee_id=vals.get('employee_id') or default) for vals in vals_list]
        leaves = super().create(vals_list)
        service = self.env['mobile.timeoff.service']
        for leave in leaves:
            service._mobile_on_state_change(leave, False, leave.state)
        return leaves

    def write(self, vals):
        # Track the state itself rather than specific action_* methods, so
        # customer modules that add states or change the approval flow still
        # trigger notifications.
        before = {leave.id: leave.state for leave in self}
        result = super().write(vals)
        service = self.env['mobile.timeoff.service']
        for leave in self:
            if before.get(leave.id) != leave.state:
                service._mobile_on_state_change(leave, before.get(leave.id), leave.state)
        return result
