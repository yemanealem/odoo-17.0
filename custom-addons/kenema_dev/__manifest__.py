# -*- coding: utf-8 -*-
{
    'name': "Kenema Pharmacy",

    'summary': """
        Kenema pharmacy Inventory module extension.""",

    'description': """
        This module is developed for Kenema Pharmacy. It works as an extension module to handle inventory operations. 
    """,

    'author': "Medco",
    'website': "https://Medco.com",

    # Categories can be used to filter modules in modules listing
    # for the full list
    'category': 'Inventory',
    'version': '1.0',

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'security/sequence.xml',
        'views/hide_default_menus.xml',
        'views/kenema_stock_transfer_custom.xml',
        'views/system_inherited.xml',
    ],

    # any module necessary for this one to work correctly

    'depends': ['base',
                'mail','stock',
                'resource',
                'web', 'crm'],
    "license": "AGPL-3",
    # only loaded in demonstration mode
    'installable': True,
    'application': True
}
