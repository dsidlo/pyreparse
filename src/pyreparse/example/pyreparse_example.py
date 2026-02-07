#!/usr/bin/env python3

'''
Example PyReParse usage...
This is a template example for creating your own PyReParse parser engine. 
'''

from pyreparse import PyReParse
from decimal import Decimal
import argparse
import sys


cb_txline_cnt = 0
cb_rptid_cnt = 0

class PyReParse_Example():
    """
    We create a class that will make use of the PyReParse module for parsing a document as a
    stream of lines that are pushed into the match() function.
    """

    def __init__(self):
        self.PRP = PyReParse
        self.prp = self.PRP()
        self.prp.load_re_lines(PyReParse_Example.test_re_lines)
        self.args = None
        self.file_path = None

    def cb_rport_id(prp_inst: PyReParse, pattern_name):
        '''
        Callback for report_id pattern.
        Callbacks can be used for editing or transforming captured values.
        They can also be used as a form of stream processing given that the sequence of lines entering
        into the PyReParse.match() function is a stream.

        Given that we have access to the PyReParse instance, we can use it to look at the states of existing
        named-patterns via the dictioary prp_inst.re_defs[<pattern-name>][PRP.INFO_STATE][PRP.INDEX_]

        :param prp_inst: An instance to the PyReParse object.
        :param pattern_name:
        :return:
        '''
        global cb_rptid_cnt

        flds = prp_inst.last_captured_fields
        for f in flds:
            None
            # print(f'{f}:[{flds[f]}], ', end='')
            # print('')

        cb_rptid_cnt += 1

    def cb_tx_line(prp_inst: PyReParse, pattern_name):
        '''
        Callback for txline pattern.

        The 'tx_line' pattern is the main data of interest.
        It really represents a customer transaction with the financial institution.
        This call back could be used to push the transaction fields into a database.

        :param prp_inst: An instance to the PyReParse object.
        :param pattern_name:
        :return:
        '''
        global cb_txline_cnt

        flds = prp_inst.last_captured_fields
        for f in flds:
            None
            # print(f'{f}:[{flds[f]}], ', end='')
            # print('')

        cb_txline_cnt += 1

    PRP = PyReParse

    '''
    This is the data structure that contains a set of RegExp(s) that will be run against a text report.
    It is important to verify the the regular expressions match to expected lines.
    If the regular expression is complex because it contains lots of capture groups, you have the option of adding an
    associated re_quick_check regular expression that can do a quick check on lines to see if they were possible
    candidates for a match. The quick_check regular expression is tested on lines that did not match to the main
    regexp, and if a match occurs, is produces a warning indicating that a line may have been missed.
    If you get the warning and find that the line should have matched, you can use that information to update the
    main regexp, such that it can capture the line of interest.
    '''
    test_re_lines = {
        'report_id': {
            self.PRP.INDEX_RE_STRING:
                r'''
                ^\*\*(?P<report_id>[^\ ]+)\s*$
                ''',
            # Flag apply specifies characteristics of the current regular expression.
            #     FLAG_RETURN_ON_MATCH
            #     : If match occurs, don't bother matching against any other RegExps.
            #     FLAG_NEW_SECTION
            #     : Reset Section Counters to 0
            #     FLAG_ONCE_PER_SECTION
            #     : Turn off further matching for this RegExp after the first match.
            #     FLAG_ONCE_PER_REPORT = 8
            #     : Turn off further matching for this RegExp after the first match.
            #     FLAG_END_OF_SECTION = 16    # Counters are set to 0
            self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_RETURN_ON_MATCH | self.PRP.FLAG_NEW_SECTION,
            # Trigger_On: When true means that this regexp will be used.
            # Trigggers perform comparisons against symbolic <COuNTERS> and boolean operations against
            # {named_patterns} that have or have not been matched. The return values of the trigger
            # should only be True or False.
            self.PRP.INDEX_RE_TRIGGER_ON: '<SECTION_LINE> == 1',
            # Trigger_Off: When true mean that this regexp will not be used.
            self.PRP.INDEX_RE_TRIGGER_OFF: '{report_id}',
            # We create a reference to the callback that we created for this field.
            # The callback is called when the pattern is matched, and after field values have been captured.
            self.PRP.INDEX_RE_CALLBACK: cb_rport_id,
        },
        'file_date': {
            self.PRP.INDEX_RE_STRING:
                r'''
                ^IPPOSFEE\s+
                FILE\ DATE:\s+(?P<file_date>[\d\/]+)
                ''',
            self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_RETURN_ON_MATCH | self.PRP.FLAG_ONCE_PER_SECTION,
            self.PRP.INDEX_RE_TRIGGER_ON: '{report_id}',
            self.PRP.INDEX_RE_TRIGGER_OFF: '{file_date}'
        },
        'run_date': {
            self.PRP.INDEX_RE_STRING:
                r'''
                ^RUN\ DATE\:\s+(?P<run_date>[\d\/]+)\s+
                RUN\ TIME\:\s+(?P<run_time>[\d\:]+)
                ''',
            self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_RETURN_ON_MATCH | self.PRP.FLAG_ONCE_PER_SECTION,
            self.PRP.INDEX_RE_TRIGGER_ON: '{file_date}',
            self.PRP.INDEX_RE_TRIGGER_OFF: '{run_date}'
        },
        'start_tx_lines': {
            self.PRP.INDEX_RE_STRING:
                r'^[\ \-]+$',
            self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_RETURN_ON_MATCH | self.PRP.FLAG_ONCE_PER_SECTION,
            self.PRP.INDEX_RE_TRIGGER_ON: '{run_date}',
            self.PRP.INDEX_RE_TRIGGER_OFF: '{start_tx_lines}'
        },
        'tx_line': {
            self.PRP.INDEX_RE_STRING:
                r'''
                ^\s+(?#This comment is needed to pick up <ac_num> regexp bug?)
                (?P<ac_num>\d+)\-(?P<ac_type>\d+)\s+
                (?P<nsf_fee>[\-\$\s\d\,]+\.\d\d)\s
                (?P<fee_code>.{2})\s
                (?P<tx_desc>.{24})\s+
                (?P<tx_amt>[\-\$\s\d\,]+\.\d\d)\s+
                (?P<tx_date>[\d\/]+)\s+
                (?P<balance>[\-\$\s\d\,]+\.\d\d)\s+
                (?P<trace_num>.{10})\s+
                (?P<tx_seq>\d+)\s\s
                (?P<fee_type>.+)
                ''',
            # The re_quick_check is used to verify check if the unmatched line is aactually a possible
            # match for the main regexp.
            're_quick_check':
                r''' (?# A simpler regexp that checks to see if a match should have occurred...)
                ^\s*\d+\-\d+\s+\$\s*[\d\.]+\s
                ''',
            self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_RETURN_ON_MATCH,
            self.PRP.INDEX_RE_TRIGGER_ON: '{start_tx_lines}',
            self.PRP.INDEX_RE_TRIGGER_OFF: '{end_tx_lines}',
            self.PRP.INDEX_RE_CALLBACK: cb_tx_line,
        },
        'end_tx_lines': {
            self.PRP.INDEX_RE_STRING:
                r'^\s+[\-]+\s*',
            self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_RETURN_ON_MATCH | self.PRP.FLAG_ONCE_PER_SECTION,
            self.PRP.INDEX_RE_TRIGGER_ON: '{tx_line}',
            self.PRP.INDEX_RE_TRIGGER_OFF: '{end_tx_lines} | {total_nsf} | {grand_total}',
        },
        'total_nsf': {
            self.PRP.INDEX_RE_STRING:
                r'^Total\ NSF:\s*(?P<total_nsf>[\-\$\ \d\,\.]+)',
            self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_RETURN_ON_MATCH | self.PRP.FLAG_ONCE_PER_SECTION,
            self.PRP.INDEX_RE_TRIGGER_ON: '{end_tx_lines}',
            self.PRP.INDEX_RE_TRIGGER_OFF: '{total_nsf}' # Insufficient Funds Total
        },
        'total_odt': {
            self.PRP.INDEX_RE_STRING:
                r'^Total\ ODT:\s*(?P<total_odt>[\-\$\ \d\,\.]+)',
            self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_RETURN_ON_MATCH | self.PRP.FLAG_ONCE_PER_SECTION,
            self.PRP.INDEX_RE_TRIGGER_ON: '{total_nsf}', # Insufficient Funds Total
            self.PRP.INDEX_RE_TRIGGER_OFF: '{total_odt}'
        },
        'grand_total': {
            self.PRP.INDEX_RE_STRING:
                r'^Grand\ Total:\s*(?P<grand_total>[\-\$\ \d\,\.]+)',
            self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_RETURN_ON_MATCH | self.PRP.FLAG_END_OF_SECTION,
            self.PRP.INDEX_RE_TRIGGER_ON: '{total_odt}', # Overdraft Total
            self.PRP.INDEX_RE_TRIGGER_OFF: '{grand_total}'
        }
    }

    def parse_file(self):
        parser = argparse.ArgumentParser(description='PyReParse Example')
        parser.add_argument('file_path', nargs='?', default='tests/data/NsfPosFees/999-063217-XXXX-PAID-NSF POS FEES CHARGED page 0001 to 0188.TXT')
        parser.add_argument('--parallel-sections', type=int, default=0, help='Parallel depth >0')
        self.args = parser.parse_args()
        self.file_path = self.args.file_path

        if self.args.parallel_sections > 0:
            sections = self.prp.parse_file_parallel(self.file_path, max_workers=4, parallel_depth=self.args.parallel_sections)
            total_matches = sum(len(s['fields_list']) for s in sections)
            print(f"Parallel depth {self.args.parallel_sections}: {len(sections)} sections, {total_matches} matches")
            # TODO aggregate totals/validations
        else:
            # Existing serial parse_file logic (cb_rport_id etc)
            report_id = ''
            file_date = ''
            run_date = ''
            run_time = ''
            txn_lines = []
            total_nsf = 0
            total_odt = 0
            grand_total = 0

            with open(self.file_path, 'r') as txt_file:
                for line in txt_file:
                    match_def, matched_fields = self.prp.match(line)
                    if match_def == ['report_id']:
                        report_id = matched_fields['report_id']
                        # Reset tx_lines array on new section...
                        txn_lines = []
                    elif match_def == ['file_date']:
                        file_date = matched_fields['file_date']
                    elif match_def == ['run_date']:
                        run_date = matched_fields['run_date']
                        run_time = matched_fields['run_time']
                    elif match_def == ['tx_line']:
                        m_flds = matched_fields
                        fld = 'nsf_fee'
                        m_flds[fld] = self.prp.money2decimal(fld, m_flds[fld])
                        fld = 'tx_amt'
                        m_flds[fld] = self.prp.money2decimal(fld, m_flds[fld])
                        fld = 'balance'
                        m_flds[fld] = self.prp.money2decimal(fld, m_flds[fld])
                        txn_lines.append(m_flds)
                    elif match_def == ['end_tx_lines']:
                        pass
                    elif match_def == ['total_nsf']:
                        m_flds = matched_fields
                        fld = 'total_nsf'
                        total_nsf = self.prp.money2decimal(fld, m_flds[fld])
                    elif match_def == ['total_odt']:
                        m_flds = matched_fields
                        fld = 'total_odt'
                        total_odt = self.prp.money2decimal(fld, m_flds[fld])
                    elif match_def == ['grand_total']:
                        m_flds = matched_fields
                        fld = 'grand_total'
                        grand_total = self.prp.money2decimal(fld, m_flds[fld])

                        # Run totals & validations
                        nsf_tot = Decimal('0')
                        for flds in txn_lines:
                            nsf_tot += flds['nsf_fee']

                        if nsf_tot == grand_total:
                            print(f'*** Section [{self.prp.section_count}] Parsing Completed.')

                        # Reset tx_lines array at end of section...
                        txn_lines = []

            if self.prp.section_count == 2538:
                print('\n*** All Sections Processed!')

if __name__ == '__main__':
    example = PyReParse_Example()
    example.parse_file()
