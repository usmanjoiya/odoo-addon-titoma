# Product TIS URL Module

This is an Odoo module developed by TITOMA Design LTD. It adds a new field, `TIS URL`, to the Products module in Odoo.

## Features

- Adds a `TIS URL` field to the `product.template` model. The value of this field is computed based on the `default_code` field of the product. The computation is defined in the [`ProductTemplate._compute_tis_url`](models/product_template.py) method in [models/product_template.py](models/product_template.py).
- The `TIS URL` field is added to the product form view, right after the `categ_id` field. This is defined in the [product_template_views.xml](views/product_template_views.xml) file.

## Installation

To install this module, you need to:

1. Download or clone this repository into your Odoo addons folder.
2. Update the addons list in your Odoo instance.
3. Install the module from the apps menu.

Please note that this module depends on the `sale_stock` module, so make sure that module is installed in your Odoo instance.

## Usage

Once installed, the `TIS URL` field will be automatically computed for all products based on their `default_code`. You can see this field in the product form view.

## Author

This module was created by TITOMA Design LTD.