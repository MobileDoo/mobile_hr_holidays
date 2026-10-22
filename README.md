# Mobile Time Off (`mobile_hr_holidays`)

Time Off API for the MobileDoo app, with hooks for customer extensions.

Odoo addon for [MobileDoo](https://github.com/MobileDoo), the mobile app for Odoo. This branch (`18.0`) is for **Odoo 18**; every supported Odoo version has its own branch with the same addon name.

## Installation

Requires [`mobile_connector`](https://github.com/MobileDoo/mobile_connector) (same branch) and the Odoo module(s) `hr_holidays`.

Add this repository to `addons_path` (the addon is the `mobile_hr_holidays/` folder at the root) and install `mobile_hr_holidays` from *Apps*, or:

```bash
odoo -d <database> -i mobile_hr_holidays --stop-after-init
```

The addon installs itself automatically once its dependencies are installed (`auto_install`).

## License

LGPL-3 - see [LICENSE](LICENSE).
