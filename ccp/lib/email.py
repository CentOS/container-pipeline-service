#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from ccp.lib.command import run_cmd


class SendEmail(object):
    """
    This class has related methods for sending email
    """
    def escape_text(self, text):
        """
        Given text, escapes newlines and tabs
        """
        return text.replace("\n", "\\n").replace("\t", "\\t")

    def email(self,
              smtp_server, sub, body,
              from_add, to_adds, cc_adds=[]):
        """
        Send email using given details
        smtp_server: URL of smtp server
        sub: Subject of email
        body: Body of email
        from_add: From address
        to_adds: A list of to addresses
        cc_adds: (optional) A list addresses to mark in Cc
        """
        command = """\
echo -e '{body}' | mail -r {from_address} {cc_opts} -S \
{smtp_server} -s "{subject}" {to_addresses}"""

        # it would return '' for when cc_add==[]
        # eg output: "-c a@mail.com -c b@mail.com"
        cc_opts = " ".join(["-c " + i for i in cc_adds])

        # to addresses
        to_addresses = " ".join(to_adds)

        # escape the \n and \t characters
        body = self.escape_text(body)

        command = command.format(
            body=body,
            from_address=from_add,
            cc_opts=cc_opts,
            smtp_server=smtp_server,
            subject=sub,
            to_addresses=to_addresses)

        # send email
        run_cmd(command, shell=True)
        print ("Email sent to {}".format(to_adds))
