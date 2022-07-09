#!/usr/bin/env python3

import sys
import re
import os
import unittest

'''
Tests for pyreparse module...
'''

import inspect
from pyreparse import PyReParse

class TestPyReParse(unittest.TestCase):

    rtrpc = PyReParse

    in_line_0 = r'''**BP0420170101REPOREPOPAID-NSFPOSF00016-38864369
'''
    in_line_1 = r'''IPPOSFEE             FILE DATE: 12/31/15              SAN MATEO CREDIT UNION                 RPPOSRPT                    PAGE:    1
'''
    in_line_2 = r'''RUN DATE: 01/01/16   RUN TIME:  00:14:18            Paid-NSF POS Fees Charged
'''
    in_line_3 = r'''------------  ------- -- ------------------------  ----------  ---------  -----------  ----------  ---------  ---------                                                                  
'''
    in_line_4 = r'''   342568-80  $  0.00    VALLARTA SUPERMARK ARVIN  $     5.41  01/02/16    $     0.00  120104028       71567  ZERO OVERDRAFT FEE                                                         

'''

    '''
    This is the data structure that contains a set of RegExp(s) that will be run against a text report.
    It is important to verify the the regular expressions match to expected lines.
    If the regular expression is complex because it contains lots of capture groups, you have the option of adding an
    associated re_quick_check regular expression that can do a quick check on lines to see if they were possible \
    candidates for a match. The quick_check regular expression is tested on lines that did not match to the main
    regexp, and if a match occurs, is produces a warning indicating that a line may have been missed. 
    If you get the warning and find that the line should have matched, you can use that information to update the 
    main regexp, such that it can capture the line of interest.

    TODO: Add an "edit" entry (refer to a function that will edit/conert the captured string)
    TODO: A validation option that check to see that all lines between 2 regexp-defs matched to a given regexp-def
          is to count the blank and non-blank lines between the 2 bounding regexp-defs and run an appropriate
          calculation and match against the total matches of the regexp-def in question.
    '''
    test_re_lines = {
        'report_id': {
            're_string':
                r'''
                ^\*\*(?P<report_id>[^\ ]+)\s*$
                ''',
            'flags': rtrpc.FLAG_RETURN_ON_MATCH | rtrpc.FLAG_RESET_SECTION_LINE,
            # Trigger Matching on (dependant fields)...
            # {LINE}[n]         Line == n
            # {START_LINE}[n]... Line >= n, to Turn off see below: {END_LINE}[n]... Line < n
            'trigger_on': '',
            # Turn off Matching on...
            # {END_LINE}[n]... Line < n
            'trigger_off': 'report_id'
        },
        'file_date': {
            're_string':
                r'''
                ^IPPOSFEE\s+
                FILE\ DATE:\s+(?P<file_date>[\d\/]+)
                ''',
            'flags': rtrpc.FLAG_RETURN_ON_MATCH | rtrpc.FLAG_ONCE_PER_SECTION,
            # Trigger Matching on (dependant fields)...
            # {LINE}[n]         Line == n
            # {START_LINE}[n]... Line >= n, to Turn off see below: {END_LINE}[n]... Line < n
            # 'trigger_on': f'{rtrpc.TRIG_START_SECTION_LINE}[1]',
            'trigger_on': 'report_id',
            # Turn off Matching on...
            # {END_LINE}[n]... Line < n
            # 'trigger_off': f'{rtrpc.TRIG_END_SECTION_LINE}[3] | file_date'
            'trigger_off': 'file_date'
        },
        'run_date': {
            're_string':
                r'''
                ^RUN\ DATE\:\s+(?P<run_date>[\d\/]+)\s+
                RUN\ TIME\:\s+(?P<run_time>[\d\:]+)
                ''',
            'flags': rtrpc.FLAG_RETURN_ON_MATCH | rtrpc.FLAG_ONCE_PER_SECTION,
            'trigger_on': 'file_date',
            'trigger_off': 'run_date'
        },
        'start_tx_lines': {
            're_string':
                r'^[\ \-]+$',
            'flags': rtrpc.FLAG_RETURN_ON_MATCH | rtrpc.FLAG_ONCE_PER_SECTION,
            'trigger_on': 'run_date',
            'trigger_off': 'start_tx_lines'
        },
        'tx_line': {
            're_string':
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
            're_quick_check':
                ''' (?# A simpler regexp that checks to see if a match should have occurred...)
                ^\s*\d+\-\d+\s+\$\s*[\d\.]+\s
                ''',
            'flags': rtrpc.FLAG_RETURN_ON_MATCH,
            'trigger_on': 'start_tx_lines',
            'trigger_off': 'end_tx_lines'
        },
        'pos_tx_line': {
            'positional': {
                'ac_num': ['String', 6, 14],
                'nsf_fee': ['Money', 0, 1, 23],
                'fee_code': ['String', 25, 26],
                'tx_desc': ['String', 28, 51],
                'tx_amt': ['Money', 53, 55, 63],
                'tx_date': ['String', 66, 73],
                'balance': ['Money', 77, 79, 87],
                'trace_num': ['Integer', 0, 90, 99],
                'tx_seq': ['Integer', 0, 102, 110],
                'fee_type': ['String', 113, 132]
            },
            're_quick_check':
                '''
                ^\s*\d+\-\d+\s+\$\s*[\d\.]+\s
                ''',
            'flags': rtrpc.FLAG_RETURN_ON_MATCH,
            # 'trigger_on': '{START_LINE}[4]|start_tx_lines',
            'trigger_on': 'start_tx_lines',
            'trigger_off': 'end_tx_lines'
        },
        'end_tx_lines': {
            're_string':
                r'^\s+[\-]+\s*',
            'flags': rtrpc.FLAG_RETURN_ON_MATCH | rtrpc.FLAG_ONCE_PER_SECTION,
            'trigger_on': 'tx_line',
            'trigger_off': 'end_tx_lines'
        },
        'total_nsf': {
            're_string':
                r'^Total\ NSF:\s*(?P<total_nsf>[\-\$\ \d\,\.]+)',
            'flags': rtrpc.FLAG_RETURN_ON_MATCH | rtrpc.FLAG_ONCE_PER_SECTION,
            'trigger_on': 'end_tx_lines',
            'trigger_off': 'total_nsf'
        },
        'total_odt': {
            're_string':
                r'^Total\ ODT:\s*(?P<total_odt>[\-\$\ \d\,\.]+)',
            'flags': rtrpc.FLAG_RETURN_ON_MATCH | rtrpc.FLAG_ONCE_PER_SECTION,
            'trigger_on': 'total_nsf',
            'trigger_off': 'total_odt'
        },
        'grand_total': {
            're_string':
                r'^Grand\ Total:\s*(?P<grand_total>[\-\$\ \d\,\.]+)',
            'flags': rtrpc.FLAG_RETURN_ON_MATCH | rtrpc.FLAG_END_OF_SECTION,
            'trigger_on': 'total_odt',
            'trigger_off': 'grand_total'
        }
    }

    expected_value_1 = {'file_date': '', 'run_time': '', 'run_date': '', 'fee_type': '', 'tx_seq': '',
                        'trace_num': '', 'balance': '',
                        'tx_date': '', 'tx_amt': '', 'tx_desc': '', 'fee_code': '', 'nsf_fee': '',
                        'ac_type': '',
                        'ac_num': ''}

    expected_value_2 = ['file_date']

    expected_value_3_1 = ['run_date']
    expected_value_3_2 = {'run_date': '01/01/16', 'run_time': '00:14:18'}

    expected_value_4_1 = ['tx_line']
    expected_value_4_2 = {'ac_num': '342568',
                          'ac_type': '80',
                          'balance': '$     0.00',
                          'fee_code': '  ',
                          'fee_type': 'ZERO OVERDRAFT '
                                      'FEE                                                         ',
                          'nsf_fee': '$  0.00',
                          'trace_num': '120104028 ',
                          'tx_amt': '$     5.41',
                          'tx_date': '01/02/16',
                          'tx_desc': 'VALLARTA SUPERMARK ARVIN',
                          'tx_seq': '71567'}

    def test_load_re(self):
        rtp = PyReParse()
        fld_names = rtp.load_re_lines(TestPyReParse.test_re_lines)
        self.assertEqual(fld_names, TestPyReParse.expected_value_1)

    def test_match_1(self):
        rtp = PyReParse()
        fld_names = rtp.load_re_lines(TestPyReParse.test_re_lines)
        match_re_lines, last_captured = rtp.match(TestPyReParse.in_line_0)
        self.assertEqual(match_re_lines, ['report_id'])
        match_re_lines, last_captured = rtp.match(TestPyReParse.in_line_1)
        self.assertEqual(match_re_lines, TestPyReParse.expected_value_2)

    def test_match_2(self):
        rtp = PyReParse()
        fld_names = rtp.load_re_lines(TestPyReParse.test_re_lines)
        match_re_lines, last_captured = rtp.match(TestPyReParse.in_line_0)
        match_re_lines, last_captured = rtp.match(TestPyReParse.in_line_1)
        match_re_lines, last_captured = rtp.match(TestPyReParse.in_line_2)
        self.assertEqual(match_re_lines, TestPyReParse.expected_value_3_1)
        self.assertEqual(rtp.last_captured_fields, TestPyReParse.expected_value_3_2)

    def test_match_3(self):
        rtrpc = PyReParse
        rtp = PyReParse()
        fld_names = rtp.load_re_lines(TestPyReParse.test_re_lines)

        # Match against line_1
        match_re_lines, last_captured = rtp.match(TestPyReParse.in_line_0)
        # file_date def should have a mach attempt count of 1
        self.assertEqual(rtp.re_defs['report_id'][rtrpc.INDEX_RE_STATES][rtrpc.INDEX_RE_SECTION_LINES_MATCHED], 1)

        # Match against line_1
        match_re_lines, last_captured = rtp.match(TestPyReParse.in_line_1)
        # file_date def should have a mach attempt count of 1
        self.assertEqual(rtp.re_defs['report_id'][rtrpc.INDEX_RE_STATES][rtrpc.INDEX_RE_SECTION_LINES_MATCHED], 1)
        self.assertEqual(rtp.re_defs['file_date'][rtrpc.INDEX_RE_STATES][rtrpc.INDEX_RE_SECTION_LINES_MATCHED], 1)

        # Match against line_2
        match_re_lines, last_captured = rtp.match(TestPyReParse.in_line_2)
        # file_date def should have a mach attempt count of 1
        self.assertEqual(rtp.re_defs['report_id'][rtrpc.INDEX_RE_STATES][rtrpc.INDEX_RE_SECTION_LINES_MATCHED], 1)
        self.assertEqual(rtp.re_defs['file_date'][rtrpc.INDEX_RE_STATES][rtrpc.INDEX_RE_SECTION_LINES_MATCHED], 1)
        self.assertEqual(rtp.re_defs['run_date'][rtrpc.INDEX_RE_STATES][rtrpc.INDEX_RE_SECTION_LINES_MATCHED], 1)

        # Match against line_3
        match_re_lines, last_captured = rtp.match(TestPyReParse.in_line_3)
        self.assertEqual(match_re_lines, ['start_tx_lines'])
        # file_date def should have a mach attempt count of 1
        self.assertEqual(rtp.re_defs['report_id'][rtrpc.INDEX_RE_STATES][rtrpc.INDEX_RE_SECTION_LINES_MATCHED], 1)
        self.assertEqual(rtp.re_defs['file_date'][rtrpc.INDEX_RE_STATES][rtrpc.INDEX_RE_SECTION_LINES_MATCHED], 1)
        self.assertEqual(rtp.re_defs['run_date'][rtrpc.INDEX_RE_STATES][rtrpc.INDEX_RE_SECTION_LINES_MATCHED], 1)
        self.assertEqual(rtp.re_defs['start_tx_lines'][rtrpc.INDEX_RE_STATES][rtrpc.INDEX_RE_SECTION_LINES_MATCHED], 1)

        # Match against line_4
        match_re_lines, last_captured = rtp.match(TestPyReParse.in_line_4)
        # file_date def should have a mach attempt count of 1
        self.assertEqual(rtp.re_defs['report_id'][rtrpc.INDEX_RE_STATES][rtrpc.INDEX_RE_SECTION_LINES_MATCHED], 1)
        self.assertEqual(rtp.re_defs['file_date'][rtrpc.INDEX_RE_STATES][rtrpc.INDEX_RE_SECTION_LINES_MATCHED], 1)
        self.assertEqual(rtp.re_defs['run_date'][rtrpc.INDEX_RE_STATES][rtrpc.INDEX_RE_SECTION_LINES_MATCHED], 1)
        self.assertEqual(rtp.re_defs['start_tx_lines'][rtrpc.INDEX_RE_STATES][rtrpc.INDEX_RE_SECTION_LINES_MATCHED], 1)
        self.assertEqual(rtp.re_defs['tx_line'][rtrpc.INDEX_RE_STATES][rtrpc.INDEX_RE_SECTION_LINES_MATCHED], 1)

        # Should be the same results as test_match_2 (results don't intermingle)
        self.assertEqual(match_re_lines, TestPyReParse.expected_value_4_1)
        self.assertEqual(rtp.last_captured_fields, TestPyReParse.expected_value_4_2)

    def test_parse_file(self):
        file_path = 'data/NsfPosFees/999-063217-XXXX-PAID-NSF POS FEES CHARGED page 0001 to 0188.TXT'
        rtrpc = PyReParse
        rtp = PyReParse()
        fld_names = rtp.load_re_lines(TestPyReParse.test_re_lines)
        report_id = ''
        file_date = ''
        run_date = ''
        run_time = ''
        txn_lines = []
        total_nsf = 0
        total_odt = 0
        grand_total = 0

        with open(file_path, 'r') as txt_file:
            for line in txt_file:
                match_def, matched_fields = rtp.match(line)
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
                    m_flds[fld] = rtp.money2float(fld, m_flds[fld])
                    fld = 'tx_amt'
                    m_flds[fld] = rtp.money2float(fld, m_flds[fld])
                    fld = 'balance'
                    m_flds[fld] = rtp.money2float(fld, m_flds[fld])
                    txn_lines.append(m_flds)
                elif match_def == ['end_tx_lines']:
                    pass
                elif match_def == ['total_nsf']:
                    m_flds = matched_fields
                    fld = 'total_nsf'
                    total_nsf = rtp.money2float(fld, m_flds[fld])
                elif match_def == ['total_odt']:
                    m_flds = matched_fields
                    fld = 'total_odt'
                    total_odt = rtp.money2float(fld, m_flds[fld])
                elif match_def == ['grand_total']:
                    m_flds = matched_fields
                    fld = 'grand_total'
                    grand_total = rtp.money2float(fld, m_flds[fld])

                    # Run totals & validations
                    nsf_tot = 0
                    for flds in txn_lines:
                        nsf_tot += flds['nsf_fee']
                    self.assertEqual(nsf_tot, grand_total)

                    # Reset tx_lines array at end of section...
                    txn_lines = []

