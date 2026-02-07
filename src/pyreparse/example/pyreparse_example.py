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
            PRP.INDEX_RE_STRING:
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
            PRP.INDEX_RE_FLAGS: PRP.FLAG_RETURN_ON_MATCH | PRP.FLAG_NEW_SECTION,
            # Trigger_On: When true means that this regexp will be used.
            # Trigggers perform comparisons against symbolic <COuNTERS> and boolean operations against
            # {named_patterns} that have or have not been matched. The return values of the trigger
            # should only be True or False.
            PRP.INDEX_RE_TRIGGER_ON: '<SECTION_LINE> == 1',
            # Trigger_Off: When true mean that this regexp will not be used.
            PRP.INDEX_RE_TRIGGER_OFF: '{report_id}',
            # We create a reference to the callback that we created for this field.
            # The callback is called when the pattern is matched, and after field values have been captured.
            PRP.INDEX_RE_CALLBACK: cb_rport_id,
        },
        'file_date': {
            PRP.INDEX_RE_STRING: r'^IPPOSFEE\s+FILE\s+DATE:\s+(?P<file_date>[\d/]+).*',
            PRP.INDEX_RE_FLAGS: PRP.FLAG_RETURN_ON_MATCH | PRP.FLAG_ONCE_PER_SECTION,
            PRP.INDEX_RE_TRIGGER_ON: '{report_id}',
            PRP.INDEX_RE_TRIGGER_OFF: '{file_date}'
        },
        'run_date': {
            PRP.INDEX_RE_STRING: r'^RUN\s+DATE:\s+(?P<run_date>[\d/]+)\s+RUN\s+TIME:\s+(?P<run_time>[\d:]+).*',
            PRP.INDEX_RE_FLAGS: PRP.FLAG_RETURN_ON_MATCH | PRP.FLAG_ONCE_PER_SECTION,
            PRP.INDEX_RE_TRIGGER_ON: '{file_date}',
            PRP.INDEX_RE_TRIGGER_OFF: '{run_date}'
        },
        'start_tx_lines': {
            PRP.INDEX_RE_STRING:
                r'^[\ \-]+$',
            PRP.INDEX_RE_FLAGS: PRP.FLAG_RETURN_ON_MATCH | PRP.FLAG_ONCE_PER_SECTION,
            PRP.INDEX_RE_TRIGGER_ON: '{run_date}',
            PRP.INDEX_RE_TRIGGER_OFF: '{start_tx_lines}'
        },
        'tx_line': {
            PRP.INDEX_RE_STRING:
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
            PRP.INDEX_RE_FLAGS: PRP.FLAG_RETURN_ON_MATCH,
            PRP.INDEX_RE_TRIGGER_ON: '{start_tx_lines}',
            PRP.INDEX_RE_TRIGGER_OFF: '{end_tx_lines}',
            PRP.INDEX_RE_CALLBACK: cb_tx_line,
        },
        'end_tx_lines': {
            PRP.INDEX_RE_STRING:
                r'^\s+[\-]+\s*',
            PRP.INDEX_RE_FLAGS: PRP.FLAG_RETURN_ON_MATCH | PRP.FLAG_ONCE_PER_SECTION,
            PRP.INDEX_RE_TRIGGER_ON: '{tx_line}',
            PRP.INDEX_RE_TRIGGER_OFF: '{end_tx_lines} | {total_nsf} | {grand_total}',
        },
        'total_nsf': {
            PRP.INDEX_RE_STRING:
                r'^Total\ NSF:\s*(?P<total_nsf>[\-\$\ \d\,\.]+)',
            PRP.INDEX_RE_FLAGS: PRP.FLAG_RETURN_ON_MATCH | PRP.FLAG_ONCE_PER_SECTION,
            PRP.INDEX_RE_TRIGGER_ON: '{end_tx_lines}',
            PRP.INDEX_RE_TRIGGER_OFF: '{total_nsf}' # Insufficient Funds Total
        },
        'total_odt': {
            PRP.INDEX_RE_STRING:
                r'^Total\ ODT:\s*(?P<total_odt>[\-\$\ \d\,\.]+)',
            PRP.INDEX_RE_FLAGS: PRP.FLAG_RETURN_ON_MATCH | PRP.FLAG_ONCE_PER_SECTION,
            PRP.INDEX_RE_TRIGGER_ON: '{total_nsf}', # Insufficient Funds Total
            PRP.INDEX_RE_TRIGGER_OFF: '{total_odt}'
        },
        'grand_total': {
            PRP.INDEX_RE_STRING:
                r'^Grand\ Total:\s*(?P<grand_total>[\-\$\ \d\,\.]+)',
            PRP.INDEX_RE_FLAGS: PRP.FLAG_RETURN_ON_MATCH | PRP.FLAG_END_OF_SECTION,
            PRP.INDEX_RE_TRIGGER_ON: '{total_odt}', # Overdraft Total
            PRP.INDEX_RE_TRIGGER_OFF: '{grand_total}'
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
        else:
            sections = self.prp.parse_file(self.file_path)  # New serial

        # Common processing: print/merge sections
        total_matches = sum(len(s['fields_list']) for s in sections)
        print(f"Processed {len(sections)} sections, {total_matches} matches")
        # TODO aggregate totals/validations

if __name__ == '__main__':
    example = PyReParse_Example()
    example.parse_file()
