#!/usr/bin/env/python3
"""
# File: de-sk.py
# Author: Tomás Vírseda
# License: GPL v3
# Description:  Create a simple CSV file to be used by KB4IT/Oikos theme
                from a detailed Sparkasse CAMT CSV file
"""

import re
import sys
import csv
import uuid
from datetime import datetime

"""
Sparkasse CAMT CSV format:

HEADER = {
     0: {'de': 'Auftragskonto', 'en': 'Order account'},
     1: {'de': 'Buchungstag', 'en': 'Day of entry'},
     2: {'de': 'Valutadatum', 'en': 'Value date'},
     3: {'de': 'Buchungstext', 'en': 'Posting text'},
     4: {'de': 'Verwendungszweck', 'en': 'Purpose'},
     5: {'de': 'Glaeubiger ID', 'en': 'Creditor ID'},
     6: {'de': 'Mandatsreferenz', 'en': 'Mandate reference'},
     7: {'de': 'Kundenreferenz (End-to-End)', 'en': 'Customer reference (End-to-End)'},
     8: {'de': 'Sammlerreferenz', 'en': 'Collective order reference'},
     9: {'de': 'Lastschrift Ursprungsbetrag', 'en': 'Original direct debit amount'},
    10: {'de': 'Auslagenersatz Ruecklastschrift', 'en': 'Reimbursement of expenses for returning a direct debit'},
    11: {'de': 'Beguenstigter/Zahlungspflichtiger', 'en': 'Beneficiary/payer'},
    12: {'de': 'Kontonummer/IBAN', 'en': 'Account number', 'en': 'IBAN'},
    13: {'de': 'BIC (SWIFT-Code)', 'en': 'BIC (SWIFT code)'},
    14: {'de': 'Betrag', 'en': 'Amount'},
    15: {'de': 'Waehrung', 'en': 'Currency'},
    16: {'de': 'Info', 'en': 'Info'},
}
"""


# Dictionary of terms
oikosdict = {
    'ABSCHLUSS': 'Balance',
    'AUSLANDSUEBERWEISUNG': 'Foreign bank transfer',
    'AUSZAHL. MIT KUNDENENTGELT': 'Cashout. with customer fee',
    'BARGELDAUSZAHLUNG': 'Cash payout',
    'BARGELDEINZAHLUNG': 'Cash deposit',
    'BARGELDEINZAHLUNG SB':  'Cash deposit',
    'EINMAL LASTSCHRIFT': 'Once a year',
    'EINZELUEBERWEISUNG': 'Single transfer',
    'ENTGELTABSCHLUSS': 'Account fees',
    'ERSTLASTSCHRIFT': 'First debit',
    'FOLGELASTSCHRIFT': 'Recurring debit',
    'GUTSCHR. UEBERWEISUNG': 'Credit transfer',
    'KARTENZAHLUNG': 'Card payments',
    'LS WIEDERGUTSCHRIFT': 'Money returned to account',
    'LOHN GEHALT': 'Payroll',
    'ONLINE-UEBERWEISUNG': 'Online transfer',
    'ONLINE-UEBERWEISUNG TERM.': 'Online bank transfer',
    'SEPA-ELV-LASTSCHRIFT': 'Direct debit',
}

class Sparkasse:
    def get_timestamp(self, adate):
        return adate.strftime("%Y.%m.%d")

    def cleanup_string(self, text):
        new_text = re.sub(" +", " ", text)
        new_text = new_text.strip()
        return new_text

    def get_operation_type(self, text):
        try:
            return oikosdict[text]
        except:
            return text

    def get_data(self, filename):
        data = {}
        with open(filename, newline='') as csvfile:
            n = 0
            sheet = csv.reader(csvfile, delimiter=';', quotechar='\"')
            for row in sheet:
                if n == 0:
                    header = row
                    if len(header) != 17:
                        print ("Error. CSV format is not correct. Check CSV file '%s'." % filename)
                        exit(-1)
                else:
                    data[n] = {}
                    f = 0
                    for field in header:
                        if f == 1 or f == 2:
                            if len(row[f]) > 0:
                                adate = datetime.strptime(row[f], "%d.%m.%y")
                                data[n][f] = adate
                            else:
                                data[n][f] = ''
                        elif f == 14:
                            data[n][f] = float(row[f].replace(',', '.'))
                        else:
                            data[n][f] = self.cleanup_string(row[f])
                        f += 1
                n += 1
        print ("<-- Read file %s with %d entries successfully" % (filename, n-1))
        return data

    def analyze(self, data):
        now = self.get_timestamp(datetime.today())
        filename = "oikos-de-sk-%s.csv" % now.replace('.', '')
        writer = csv.writer(open(filename, 'w'), delimiter=',', quoting=csv.QUOTE_ALL)
        csvheader = ['Id', 'Date', 'Concept', 'Type', 'Category', 'From/To', 'Amount']
        writer.writerow(csvheader)
        for op in data:
            op_id = uuid.uuid4()
            op_date = self.get_timestamp(data[op][2])
            op_text = self.cleanup_string(data[op][4])
            op_amount = data[op][14]
            if op_amount < 0:
                op_type = 'Expense'
            else:
                op_type = 'Income'
            op_cat = self.get_operation_type(data[op][3])
            op_fromto = self.cleanup_string(data[op][11])
            csvrow = [op_id, op_date, op_text, op_type, op_cat, op_fromto, op_amount]
            writer.writerow(csvrow)
        print("--> File oikos.csv saved successfully with %d entries" % len(data))

if __name__ == '__main__':
    try:
        csvfile = sys.argv[1]
        sk = Sparkasse()
        data = sk.get_data(csvfile)
        sk.analyze(data)
    except IndexError as error:
        print ("Usage: python3 de-sk.py sparkasse_file.csv\n")
    except Exception as error:
        print(error)
