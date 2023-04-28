'''
Custom log handlers for sending log information to recipients.
'''

import logging
import smtplib
from logging.handlers import SMTPHandler
from  email.message import EmailMessage

class SSLSMTPHandler(SMTPHandler):
    '''
    An SSL handler for logging.handlers
    '''
    def emit(self, record:logging.LogRecord):
        """
        Emit a record while using an SSL mail server.
        """
        #Praise be to
        #https://stackoverflow.com/questions/36937461/
        #how-can-i-send-an-email-using-python-loggings-
        #smtphandler-and-ssl
        try:
            port = self.mailport
            if not port:
                port = smtplib.SMTP_PORT
            smtp = smtplib.SMTP_SSL(self.mailhost, port)
            msg = self.format(record)
            out = EmailMessage()
            out['Subject'] = self.getSubject(record)
            out['From'] = self.fromaddr
            out['To'] = self.toaddrs
            out.set_content(msg)
            #global rec2
            #rec2 = record
            if self.username:
                smtp.login(self.username, self.password)
            #smtp.sendmail(self.fromaddr, self.toaddrs, msg)
            #Attempting to send using smtp.sendmail as above
            #results in messages with no text, so use
            smtp.send_message(out)
            smtp.quit()
        except (KeyboardInterrupt, SystemExit):
            raise
        except: # pylint: disable=bare-except
            self.handleError(record)
