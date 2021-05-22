#!/usr/bin/env python3
import argparse
import csv
import locale
import os
from datetime import date, datetime
from typing import NamedTuple, List
from dateutil.parser import parse

import tabula

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

# HDFC Dinner 10X rewards
DINERS_SMARTBUY_PARTNERS = [
    'SMARTBUYBANGALORE',
    'FLIPKART PAYMENTSBANGALORE',
    'WWW GYFTR COMGURGAON',
    'SMARTBUY VOUCHERSNEW DELHI',
    'IRCTC SMART BUYBANGALORE',
    'AMAZON SELLER SERVICES MUMBAI'
]


class Transaction(NamedTuple):
    received: date
    details: str
    amount: float
    transaction_type: str


class TransactionWithRewards(NamedTuple):
    received: date
    details: str
    amount: float
    transaction_type: str
    rewards: float



# Convert Amount to Number
def try_sanitize_amount(amnts):
    xxx = amnts.split()
    try:
        return locale.atof(xxx[0])
    except ValueError:
        return None


# Parse Date
def try_parse_date(ds: str):
    try:
        return parse(ds)
    except:
        return None


# parses credit card statement
def yield_credit_infos(fname: str, show_diners_rewards: bool, password: str):
    res = tabula.read_pdf(fname, pages='all', stream=True, password=password)

    def try_transaction(line):
        transaction_date = line[0]
        amount = line[-1]
        details = line[1]
        transaction_date = try_parse_date(transaction_date)
        if transaction_date is None:
            # If start of line is not Date skip,
            # as it will not be Transaction
            return

        if 'Cr' in amount:
            transaction_type = 'credit'
        else:
            transaction_type = 'debit'

        amount = try_sanitize_amount(amount)

        if amount is None:
            return

        if show_diners_rewards:
            diners_rewards = 0
            if transaction_type == 'credit' and (details.find('IMPS PMT ') != -1 or amount < 100):
                diners_rewards = 0
            elif details in DINERS_SMARTBUY_PARTNERS:
                diners_rewards = amount * .33
            if transaction_type == 'credit':
                diners_rewards = diners_rewards * -1

            yield TransactionWithRewards(
                received=transaction_date.date(),
                details=details,
                amount=amount,
                transaction_type=transaction_type,
                rewards=diners_rewards
            )
        else:
            yield Transaction(
                received=transaction_date.date(),
                details=details,
                amount=amount,
                transaction_type=transaction_type,
            )

    for page in res:
        for line in page.values:
            for t in try_transaction(line):
                yield t


def get_credit_infos(fname: str, show_diners_rewards: bool, password: str) -> List[Transaction]:
    return list(yield_credit_infos(fname, show_diners_rewards, password))


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--statement-path', required=True, type=str,
                        help='path to statements pdf file or directory')
    parser.add_argument('--show-diners-rewards', type=str2bool,
                        help='show diners 10x rewards', default=False)
    parser.add_argument('--password', type=str, help='WTF is the password', required=True)
    parser.add_argument('--output-file-name', required=True, type=str)
    return parser.parse_args()


def parser(pdf_path, show_diners_rewards, password, output_file_name):
    infos = []

    if os.path.isfile(pdf_path):
        infos = get_credit_infos(pdf_path, show_diners_rewards, password)
    else:
        files = [f for f in os.listdir(pdf_path)]
        files = filter(lambda f: f.endswith(('.pdf', '.PDF')), files)
        for f in files:
            infos.extend(get_credit_infos(os.path.join(pdf_path, f), show_diners_rewards, password))

    with open(output_file_name, 'w') as f:
        writer = csv.writer(f, lineterminator='\n')
        if show_diners_rewards:
            writer.writerow(('Date', 'Transaction', 'Amount', 'Type', 'Rewards'))
        else:
            writer.writerow(('Date', 'Transaction', 'Amount', 'Type'))
        for tup in infos:
            writer.writerow(tup)


if __name__ == '__main__':
    arguments = parse_arguments()
    parser(arguments.statement_path, arguments.show_diners_rewards, arguments.password,
           arguments.output_file_name)
