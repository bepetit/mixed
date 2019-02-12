# Copyright 2018 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime
from lxml.objectify import fromstring
from lxml.etree import XMLSyntaxError

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class TransusAction(models.Model):
    _name = 'transus.action'
    _description = 'Transus Action'
    _rec_name = 'transactionid'
    _order = 'id desc'

    company_id = fields.Many2one('res.company', 'Company', required=True)

    exitcode = fields.Char(required=True)
    transactionid = fields.Char()
    msg_type = fields.Selection([
        ('sent', 'Sent'),
        ('received', 'Received'),
        ('receipt_confirmation_delivered', 'Receipt Delivered'),
        ('receipt_confirmation_delivery_error', 'Receipt Delivery Error'),
    ], 'Message Type', required=True)
    model = fields.Char()
    resid = fields.Integer()

    sent_message = fields.Text()
    res_message = fields.Text()

    is_processed = fields.Boolean()
    date_last_success = fields.Datetime()

    error_message = fields.Char()
    error_on_parsing = fields.Boolean()

    @api.model
    def date_from_transus(self, date):
        date = str(date)
        return datetime.strptime(date, '%Y%m%d').strftime('%Y-%m-%d')

    @api.model
    def do_cron_receive_message(self):
        companies = self.env['res.company'].search([])
        for company in companies:
            company.with_context(
                is_transus_cron=True
            )._do_receive_message()
        self.with_context(
            is_transus_cron=True
        ).do_process_actions()

    @api.model
    def do_process_actions(self):
        actions = self.search([
            ('is_processed', '!=', True),
            ('msg_type', '=', 'received'),
        ])
        for action in actions:
            if action.res_message:
                res = action.parse_result()
                if res:
                    # send confirm message
                    action.transus_send_receipt_confirmation_delivered()
                else:
                    # send error message
                    action.transus_send_receipt_confirmation_delivery_error()
                    action.error_on_parsing = True
                action.is_processed = True

    @api.multi
    def transus_send_receipt_confirmation_delivered(self):
        """M10120"""
        self.ensure_one()
        res = self._transus_message_M10120('0', self.transactionid)
        # TODO handle results
        # ExitCode
        return res

    @api.multi
    def transus_send_receipt_confirmation_delivery_error(self):
        """M10120"""
        self.ensure_one()
        res = self._transus_message_M10120('1', self.transactionid)
        # TODO handle results
        # ExitCode
        return res

    @api.multi
    def _transus_message_M10120(self, status, transactionid):
        """M10120"""
        self.ensure_one()
        self.company_id.ensure_one() # TODO
        client = self.company_id._get_transus_client()

        clientid = self.company_id.transus_clientid
        clientkey = self.company_id.transus_clientkey
        res = client.service.M10120(
            clientid,
            clientkey,
            transactionid,
            status
        )
        _logger.info("Transus message M10120")
        return res

    @api.multi
    def parse_result(self):
        self.ensure_one()
        res_message = self.res_message
        _logger.info("Transus parsing message:%s", res_message)
        try:
            res_message = res_message.replace("<?xml version='1.0' encoding='UTF-8'?>", "")
            msg = fromstring(res_message)
        except XMLSyntaxError:
            # TODO send error msg ?
            self.error_on_parsing = True
            return False
        created_record = self._transus_create_object_received(msg)
        if created_record:
            self.write({
                'model': created_record._name,
                'resid': created_record.id,
                'error_on_parsing': False,
                'error_message': '',
                'date_last_success': fields.Datetime.now(),
            })
        return created_record

    @api.multi
    def _transus_create_object_received(self, res_message):
        '''
        Extend this method to implement the logic of parsing the received
        message and to create the correspondent object.

        :param res_message:
        :return:
        '''
        return {}

    @api.multi
    def resend_message(self):
        self.ensure_one()
        orig_record = self.env[self.model].browse(self.resid)
        orig_record.transus_send_message(self.sent_message)

    @api.multi
    def reparse_message(self):
        self.ensure_one()

        res = self.parse_result()
        if res:
            # send confirm message
            self.transus_send_receipt_confirmation_delivered()
        else:
            # send error message
            self.transus_send_receipt_confirmation_delivery_error()
            self.error_on_parsing = True
        self.is_processed = True
