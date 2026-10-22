# Mobile Time Off

![Odoo 19.0](https://img.shields.io/badge/Odoo-19.0-714B67) ![License LGPL-3](https://img.shields.io/badge/license-LGPL--3-blue) ![Version 19.0.1.0.0](https://img.shields.io/badge/version-19.0.1.0.0-informational)

> Time Off API for the MobileDoo app, with hooks for customer extensions.

Odoo 19 addon of [MobileDoo](https://github.com/MobileDoo) (`mobile_hr_holidays`).

## Overview

Time Off in the MobileDoo app: request leave, see balances, and approve or refuse requests, all through the *real* `hr.leave` form and
buttons so company rules, custom fields and approval flows apply unchanged.

## Features

- **Dashboard** with balances per leave type (allocations included), upcoming leave and the number of requests waiting for the user.
- **Requests**: create, edit and submit through the server-computed form (`hr.leave` form view with its `onchange`, constraints and
  customer extensions).
- **Approvals** by officers and managers (scope `to_approve`), using Odoo's own buttons (approve, validate, refuse) and the generic
  wizard support when Odoo asks for a reason.
- **Team view** of colleagues' leave.
- **Push**: the employee is told when a request is approved or refused; approvers are notified through the activity push of the core.
- Cards for the management overview: `timeoff_to_approve` and `timeoff_today` (who is away today).
- Live updates: the dashboard version includes allocations, because balances depend on them.

## Requirements

| | |
|---|---|
| Odoo | 19.0 (Community or Enterprise) |
| Odoo modules | `hr_holidays` |
| MobileDoo addons | [`mobile_connector`](https://github.com/MobileDoo/mobile_connector/tree/19.0) (same branch) |
| Client | the [MobileDoo](https://github.com/MobileDoo) app for Android and iPhone |

This branch targets **Odoo 19** only; use the branch of your Odoo version.

## Installation

```bash
git clone --branch 19.0 https://github.com/MobileDoo/mobile_hr_holidays.git
git clone --branch 19.0 https://github.com/MobileDoo/mobile_connector.git
# add the cloned folders to addons_path in odoo.conf, then:
odoo -d <database> -i mobile_hr_holidays --stop-after-init
```

The addon is the `mobile_hr_holidays/` folder at the root of the repository, so the repository folder itself can go on `addons_path`.

`auto_install` is set: Odoo installs `mobile_hr_holidays` by itself as soon as all its dependencies are installed, so putting the folders on `addons_path` and updating the Apps list is enough.

To upgrade after pulling a newer version: `odoo -d <database> -u mobile_hr_holidays --stop-after-init`.

## How it works

| Piece | Technical detail |
|---|---|
| Record service | `timeoff` on `hr.leave`, scopes `mine` (needs `request`), `to_approve` (`approve`), `team` (`team`) |
| Endpoint | `POST /mobile/api/v1/timeoff/dashboard` returns `{employee, balances, upcoming, to_approve_count, is_officer, is_approver, today, state_selection, version}` |
| Change key | `timeoff.dashboard` |
| Services | `mobile.timeoff.service` (`_mobile_spec`, `_mobile_domain`, `_mobile_on_state_change`, `_mobile_dashboard`) |
| Extended models | `hr.leave` (mobile hooks), `mobile.api`, `mobile.dashboard.service`, `mobile.record.service` |

### Capabilities

| Capability | Granted when |
|---|---|
| `request` | the user has a linked employee and may create `hr.leave` |
| `approve` | member of `hr_holidays.group_hr_holidays_responsible` or `hr_holidays.group_hr_holidays_user`; also unlocks the management overview |
| `team` | the user has a linked employee |

Nothing is bypassed: every read and write goes through the ORM as the signed-in user, with Odoo's access rights and record rules.

## Security

No groups or ACLs are added. A user without read access to `hr.leave` has no `timeoff` feature at all, and the routes answer
`403 feature_denied`.

## Extending

The addon is built as the reference for customer extensions: add a field to `hr.leave` and list it in `_mobile_extra_fields`, then
control its visibility with the form view's own `invisible` / `readonly` / `required` expressions. New states, buttons and approval
steps added to the form header appear in the app automatically.

```python
class MobileTimeoffService(models.AbstractModel):
    _inherit = 'mobile.timeoff.service'

    @api.model
    def _mobile_extra_fields(self):
        return super()._mobile_extra_fields() + [{'name': 'handover_user_id', 'sequence': 10}]
```

To change who sees what in a list (for example a custom approval step), override `_mobile_domain(scope, params)`.

## Contributing

Issues and pull requests are welcome. Open pull requests against the branch of the Odoo version you are fixing (this one is `19.0`) and
keep the change inside the `mobile_hr_holidays/` folder.

These repositories are published from MobileDoo's development repository, which remains the source of truth. A merged pull request is
taken back there, and the branches of the other Odoo versions are updated by the maintainers, so a fix is usually welcome even if you can
only test it on one version. `README.md` and `LICENSE` are generated at each release; changes to them are not carried back.

## License

LGPL-3: see [LICENSE](LICENSE).
