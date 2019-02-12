# Copyright 2018 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import base64
from suds.client import Client
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class TransusMixin(models.AbstractModel):
    _name = 'transus.mixin'

    transus_clientid = fields.Char(compute='_compute_transus_client_parameter')
    transus_clientkey = fields.Char(compute='_compute_transus_client_parameter')
    transus_test_mode = fields.Boolean(compute='_compute_transus_client_parameter')

    @api.multi
    def _compute_transus_client_parameter(self):
        company = self.env.user.company_id
        for item in self:
            if item.fields_get(['company_id']) and item.company_id:
                company = item.company_id
            clientid = company.param_transus_clientid
            client_key = company.param_transus_clientkey
            test_mode = company.set_test_mode
            if self.env.context.get('force_test_mode'):
                test_mode = True
            item.transus_clientid = clientid
            item.transus_clientkey = client_key
            item.transus_test_mode = test_mode

    @api.model
    def _get_transus_client(self):
        if not self.env.context.get('is_transus_cron'):
            self._check_transus_config()
        wsdl = self.env['ir.config_parameter'].get_param('transus.wsdl')
        try:
            res = Client(wsdl, timeout=5)
        except Exception:
            # TODO refine handling of exceptions
            raise UserError('An error occurred while connecting to Transus.')
        return res

    def _check_transus_config(self):
        wsdl = self.env['ir.config_parameter'].get_param('transus.wsdl')
        if not wsdl:
            raise UserError('Config parameter transus.wsdl not set.')
        clientid = self.env.user.company_id.param_transus_clientid
        if not clientid:
            raise UserError('Transus Client ID not set.')
        client_key = self.env.user.company_id.param_transus_clientkey
        if not client_key:
            raise UserError('Transus Client Key not set.')

    @api.model
    def date_to_transus(self, date):
        return datetime.strptime(date, '%Y-%m-%d').strftime('%Y%m%d')

    @api.multi
    def _check_transus_required_fields(self):
        self.ensure_one()
        transus_gln = self.env.user.company_id.transus_gln
        if not transus_gln:
            raise UserError('The GLN of the Company is not set.')

    @api.model
    def _get_transus_exit_code(self, code):
        exit_codes = {
            '0': _('Successful completion'),
            '10': _('The Client ID, Client key or IP address is invalid'),
            '20': _('The access has been denied for this client'),
            '90': _('Restriction occurred'),
            '99': _('An error has occurred'),
        }
        return exit_codes[code]

    @api.multi
    def _transus_message_M10100(self, binary_msg):
        """M10100"""
        self.ensure_one()
        client = self._get_transus_client()
        msg = base64.b64encode(binary_msg).decode('UTF-8')

        res = client.service.M10100(
            self.transus_clientid,
            self.transus_clientkey,
            msg
        )
        _logger.info("Transus message M10100:%s", msg)
        return res, binary_msg

    @api.model
    def _transus_message_M10110(self):
        """M10110"""
        client = self._get_transus_client()

        res = client.service.M10110(
            self.transus_clientid,
            self.transus_clientkey,
        )
        return res

    @api.model
    def _check_transus_response(self, res):
        exit_code = self._get_transus_exit_code(res.ExitCode)
        if exit_code != '0':
            # TODO handle error
            _logger.info("Transus error with ExitCode:%s (%s)", res.ExitCode, exit_code)

    @api.multi
    def transus_test_message(self):
        self.ensure_one()
        res, binary_msg = self._transus_message_M10100(b'test')
        self._check_transus_response(res)
        action = self._store_transus_action(res, binary_msg=b'test')
        action.is_processed = True
        # TODO handle results
        # TransactionID
        # ExitCode

    @api.multi
    def transus_send_message(self, binary_msg):
        """M10100"""
        self.ensure_one()
        res, binary_msg = self._transus_message_M10100(binary_msg)
        self._check_transus_response(res)
        action = self._store_transus_action(res, binary_msg=binary_msg)
        action.is_processed = True
        # TODO handle results
        # TransactionID
        # ExitCode

    @api.multi
    def _store_transus_action(self, res, binary_msg=None):
        self.ensure_one()

        if self.fields_get(['company_id']) and self.company_id:
            company = self.company_id
        else:
            company = self
        transus_action_vals = {
            'transactionid': res.TransactionID,
            'msg_type': 'sent',
            'exitcode': res.ExitCode,
            'model': self._name,
            'resid': self.id,
            'company_id': company.id,
            'sent_message': binary_msg or '',
        }
        action = self.env['transus.action'].create(transus_action_vals)
        return action

    def _prepare_transus_xml_message(self):
        return {}

    @api.multi
    def _to_transus(self):
        self.ensure_one()
        self._check_transus_required_fields()
        xml = self._prepare_transus_xml_message()
        self.transus_send_message(xml)

    @api.multi
    def to_transus(self):
        self.ensure_one()
        self._to_transus()

    @api.multi
    def to_transus_test(self):
        self.with_context(
            force_test_mode=True
        )._to_transus()

    @api.multi
    def from_transus_test(self):
        self.ensure_one()
        self._check_transus_required_fields()
        xml = self._prepare_transus_xml_message()
        # TODO create action
        # action = ...
        # action.parse_result()
