# Copyright 2018 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _name = 'res.company'
    _inherit = ['res.company', 'transus.mixin']

    param_transus_clientid = fields.Char(string='Client ID')
    param_transus_clientkey = fields.Char(string='Client key')
    set_test_mode = fields.Boolean(default=True)
    transus_gln = fields.Char(related='partner_id.transus_gln')

    @api.multi
    def _do_receive_message(self):
        self.ensure_one()

        if not self.param_transus_clientid or not self.param_transus_clientkey:
            _logger.debug("Transus clientid/clientkey not set for:%s", self.name)
            return

        if not self.transus_gln:
            _logger.debug("Transus GLN not set for:%s", self.name)
            return

        res = self.transus_receive_message()

        if 'TransactionID' not in res:
            _logger.info("Transus TransactionID not in res:%s", self.name)
            return

        res_message = ''
        if 'Message' in res:
            res_message = str(res.Message)
            res_message = base64.b64decode(res_message).decode('utf-8')
            _logger.info("Transus received message:%s", res_message)
        else:
            _logger.info("Transus no messages found for:%s", self.name)

        res_transactionid = ''
        if 'TransactionID' in res:
            res_transactionid = res.TransactionID

        if res_message:
            transus_action_vals = {
                'transactionid': res_transactionid,
                'msg_type': 'received',
                'exitcode': res.ExitCode,
                'res_message': res_message,
                'is_processed': False,
                'company_id': self.id,
            }
            self.env['transus.action'].create(transus_action_vals)

    @api.model
    def transus_receive_message(self):
        """M10110"""
        res = self._transus_message_M10110()
        self._check_transus_response(res)
        # TODO handle results
        # TransactionID
        # Message
        # ExitCode
        return res

    @api.multi
    def test_transus(self):
        self.ensure_one()
        self.transus_test_message()
