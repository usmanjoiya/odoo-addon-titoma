#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
project_code.py
List Project Code and Project Stage.
"""
import logging

import odoo
from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)


class ProjectCode(models.Model):
    """
    Project Code
    This class defines the model for project code. The project code is used to keep
    track of different projects in the system. It has two fields, name (the code
    for the project) and description (a text field to describe the project).

    [project.code]
    """

    _name = 'project.code'
    _description = 'Project Code'

    name = fields.Char(string='Code', help='Name of Project Code.', required=True)
    description = fields.Text(string='Description', help='Description of Project Code.')
