# Changelog

All notable changes to this project will be documented in this file.

## [15.0.0.0.4] - 2023-03-05

## Features

- Make Project Code List View editable and remove form view

## [15.0.0.0.3] - 2023-03-05

### Miscellaneous Tasks

- Update zh_TW translation for project_code fields
- Remove extra picking form and .
- Remove unnecessary "widget='many2one_tags'" attribute.
- Rename project_code_menus.xml to project_code_views.xml

## [15.0.0.0.2] - 2023-02-27

### Documentation

- Clarify comments in code.
- Add comments to menuitem.
- Add string and help for all fields.
- Add zh-tw translations for i18n.
- Add `.md` extension to `CHANGELOG` to become `CHANGELOG.md`.
- Remove description from manifest and convert `README.md` to `README.rst`
- Fix images in README.rst and adjust punctuation and spacing.

### Features

- Add support for MRP and MRP document, and Purchase document.
- Restrict sales/purchase/stock user full-access to manager and add account manager.

### Miscellaneous Tasks

- Set correct chmod permission.

### Refactor

- Split models/views into separate files.
- Remove many2one_tags widget.
- Rename fileld name for clarity.
- Rename record id and field name for clarity.
- Remove unused `res` variable from overwrite action_confirm.
- Update dependencies in manifest to include mrp, sale_stock and purchase_stock.

## [15.0.0.0.1] - 2023/02/23

### added

- add project code model CRUD and ACL
- add project code and project stage in S/O , P/O , M/O , invoice , and  picking 
- The project code and stage can be input into the invoice and picking thrown out by S/O and P/O.
