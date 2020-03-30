#!/usr/bin/env/python3

import os
import re
import sys
import csv
import uuid
from datetime import datetime

# Header details
header = {
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


# Terms dictionary
## Field 03: Buchungstext / Posting text (Operation category?)
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
    'LOHN  GEHALT': 'Payroll',
    'ONLINE-UEBERWEISUNG': 'Online transfer',
    'ONLINE-UEBERWEISUNG TERM.': 'Online bank transfer',
    'SEPA-ELV-LASTSCHRIFT': 'Direct debit',
}

class CAMT:
    ops = {}
    report = {}
    output_simple = ''
    output_details = ''

    def cleanup_string(self, text):
        return re.sub(" +", " ", text)

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
        return data


    def get_timestamp(self, adate):
        return adate.strftime("%Y.%m.%d")


    def get_category_operations(self, data, category):
        lines = []
        for operation in data:
            opcat = data[operation][3]
            if opcat == category:
                opts = self.get_timestamp(data[operation][1])
                subject = data[operation][4]
                sep = subject.find('/')
                if sep > 1:
                    opsb = subject[:sep]
                else:
                    opsb = subject
                opbn = data[operation][11]
                opvl = data[operation][14]
                lines.append([opts, opsb, opbn, opvl])
        return lines

    def analyze(self, data):
        first = data[1][1]
        last = data[len(data)][1]
        delta = first - last

        incomes = 0
        expenses = 0
        amounts = {}
        for operation in data:
            postingtext = data[operation][3]
            amount = data[operation][14]
            try:
                total = amounts[postingtext]
                total += amount
                amounts[postingtext] = total
            except:
                amounts[postingtext] = amount

        for cat in amounts:
            amount = amounts[cat]
            if amount >= 0:
                incomes += amount
            else:
                expenses += amount

        self.report['first_op'] = self.get_timestamp(first)
        self.report['last_op'] = self.get_timestamp(last)
        self.report['numops'] = len(data)
        self.report['numdays'] = delta.days
        self.report['total_incomes'] = incomes
        self.report['total_expenses'] = expenses
        self.report['balance'] = incomes + expenses

        output = "Dataset corresponds to %d days with %d operations, from %s to %s\n" % (delta.days, len(data), self.get_timestamp(last), self.get_timestamp(first))
        self.output_simple += output
        self.output_details += output
        output = "\t Total incomes: %10.2f\n" % incomes
        self.output_simple += output
        self.output_details += output

        for category in amounts:
            amount = amounts[category]
            if amount >= 0:
                output = "\t\t%s = %10.2f\n" % (category + ' (' + self.get_operation_type(category) + ')' , amount)
                self.output_simple += output
                self.output_details += output
                lines = self.get_category_operations(data, category)
                for line in lines:
                    oid = uuid.uuid4()
                    self.ops[oid] = {}
                    self.ops[oid]['type'] = 'income'
                    self.ops[oid]['category'] = self.get_operation_type(category)
                    self.ops[oid]['date'] = line[0]
                    self.ops[oid]['concept'] = line[1]
                    self.ops[oid]['from_to'] = line[2]
                    self.ops[oid]['amount'] = line[3]
                    self.output_details += "\t\t\t%s - %s - %60s - %7s\n" % (line[0], line[1], line[2], line[3])
                self.output_details += "\n"
        output = "\n"
        self.output_simple += output
        self.output_details += output

        output = "\tTotal expenses: %10.2f\n" % expenses
        self.output_simple += output
        self.output_details += output
        for category in amounts:
            amount = amounts[category]
            if amount < 0:
                output = "\t\t%s = %10.2f\n" % (category + ' (' + self.get_operation_type(category) + ')', amount)
                self.output_simple += output
                self.output_details += output
                lines = self.get_category_operations(data, category)
                for line in lines:
                    oid = uuid.uuid4()
                    self.ops[oid] = {}
                    self.ops[oid]['type'] = 'expense'
                    self.ops[oid]['category'] = self.get_operation_type(category)
                    self.ops[oid]['date'] = line[0]
                    self.ops[oid]['concept'] = line[1]
                    self.ops[oid]['from_to'] = line[2]
                    self.ops[oid]['amount'] = line[3]
                    self.output_details += "\t\t\t%s - %s - %60s - %7s\n" % (line[0], line[1], line[2], line[3])
                self.output_details += "\n"
        output = "\n"
        self.output_simple += output
        self.output_details += output

        output = "\t       Balance: %10.2f\n" % (incomes + expenses)
        self.output_simple += output
        self.output_details += output

    def get_output_details(self):
        return self.output_details

    def get_output_simple(self):
        return self.output_simple

    def get_operations(self):
        return self.ops

    def get_report(self):
        return self.report
