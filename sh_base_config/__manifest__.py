# -*- coding: utf-8 -*-
{
    "name": "SH Ingeniería - Configuración Base",

    "version": "1.0.0",

    "summary": "Default settings for SH Ingeniería (Colombia)",

    "description": """
Sets the default identification type and format to NIT for new partners.
This is a permanent configuration that applies to any database
where this module is installed.
    """,

    "category": "Custom",

    "author": "Conecta",

    "website": "https://conecta.sh",

    "license": "OPL-1",

    "depends": [
        "l10n_co",
    ],

    "data": [
        "data/ir_default_data.xml",
    ],

    "installable": True,

    "application": False,

    "auto_install": False,

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
