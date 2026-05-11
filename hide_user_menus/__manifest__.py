# -*- coding: utf-8 -*-
{
    'name': 'Show User Menus (Top Right Corner)',
    'author': 'Asheal Gupta',
    'category': 'Tools',
    "license": "LGPL-3",
    'summary': 'This module hides the user menu from the top right corner of the Odoo interface, removing options like Documentation, Support, Shortcuts for a cleaner and more focused UI.',
    'maintainer': 'Asheal Gupta',
    'website': 'https://github.com/ashealgupta',
    'version': '1.0',
    'depends': ['base', 'web'],
    'assets': {
        'web.assets_backend': [
            'hide_user_menus/static/src/js/user_menus.js',
        ],
    },

    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
