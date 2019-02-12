# Copyright 2018 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Transus',
    'summary': 'Base module of a Transus connector',
    'license': 'AGPL-3',
    'author': 'Onestein',
    'website': 'http://www.onestein.eu',
    'category': 'Technical Settings',
    'version': '10.0.1.0.0',
    'depends': [
        'base',
        # 'partner_identification_gln',  # TODO evaluate adoption of this OCA module
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/transus_security_rule.xml',
        'data/ir_config_parameter_data.xml',
        'data/ir_cron.xml',
        'views/res_company_view.xml',
        'views/res_partner_view.xml',
        'views/transus_action.xml',
    ],
}
