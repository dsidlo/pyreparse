#!/usr/bin/env python3

import unittest
from pyreparse import PyReParse
from decimal import Decimal
from collections import defaultdict
import io
from contextlib import redirect_stdout

import os
import tempfile
import random
import time

from pyreparse.PyReParse import TriggerDefException

'''
Tests for pyreparse module...
'''

global cb_txline_cnt, cb_rptid_cnt
cb_txline_cnt = 0
cb_rptid_cnt = 0

class TestPyReParse(unittest.TestCase):

    PRP = PyReParse

    in_line_0 = r'''**BP0420170101REPOREPOPAID-NSFPOSF00016-95214549                                                                                     '''
    in_line_1 = r'''IPPOSFEE             FILE DATE: 12/31/15              SALLY'S EELS AND STEAKS                 RPPOSRPT                    PAGE:    1 '''
    in_line_2 = r'''RUN DATE: 01/01/16   RUN TIME:  00:14:18            Paid-NSF POS Fees Charged                                                        '''
    in_line_3 = r'''------------  ------- -- ------------------------  ----------  ---------  -----------  ----------  ---------  ---------              '''
    in_line_4 = r'''   394654-54  $  0.00    VALLARTA SUPERMARK ARVIN  $     5.41  01/02/16    $     0.00  658524658       56546  ZERO OVERDRAFT FEE     '''

    def cb_rport_id(prp_inst: PyReParse, pattern_name):
        '''
        Callback for report_id pattern.

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

    '''
    This is the data structure that contains a set of RegExp(s) that will be run against a text report.
    It is important to verify the the regular expressions match to expected lines.
    If the regular expression is complex because it contains lots of capture groups, you have the option of adding an
    associated re_quick_check regular expression that can do a quick check on lines to see if they were possible
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
            PRP.INDEX_RE_STRING:
                r'''
                ^\*\*(?P<report_id>[^\ \n]+)\s*$
                ''',
            PRP.INDEX_RE_FLAGS: PRP.FLAG_RETURN_ON_MATCH | PRP.FLAG_NEW_SECTION,
            # Trigger Matching on (dependant fields)...
            # {LINE}[n]         Line == n
            # {START_LINE}[n]... Line >= n, to Turn off see below: {END_LINE}[n]... Line < n
            PRP.INDEX_RE_TRIGGER_ON: '<SECTION_LINE> == 1',
            # Turn off Matching on...
            # {END_LINE}[n]... Line < n
            PRP.INDEX_RE_TRIGGER_OFF: '{report_id}',
            PRP.INDEX_RE_CALLBACK: cb_rport_id,
        },
        'file_date': {
            PRP.INDEX_RE_STRING: r'^IPPOSFEE\s+FILE\s+DATE:\s+(?P<file_date>[\d/]+).*',
            PRP.INDEX_RE_FLAGS: PRP.FLAG_RETURN_ON_MATCH | PRP.FLAG_ONCE_PER_SECTION,
            # Trigger Matching on (dependant fields)...
            # {LINE}[n]         Line == n
            # {START_LINE}[n]... Line >= n, to Turn off see below: {END_LINE}[n]... Line < n
            # PRP.INDEX_RE_TRIGGER_ON: f'{PRP.TRIG_START_SECTION_LINE}[1]',
            PRP.INDEX_RE_TRIGGER_ON: '{report_id}',
            # Turn off Matching on...
            # {END_LINE}[n]... Line < n
            # PRP.INDEX_RE_TRIGGER_OFF: f'{PRP.TRIG_END_SECTION_LINE}[3] | file_date'
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
            PRP.INDEX_RE_QUICK_CHECK:
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
            PRP.INDEX_RE_TRIGGER_OFF: '{total_nsf}'
        },
        'total_odt': {
            PRP.INDEX_RE_STRING:
                r'^Total\ ODT:\s*(?P<total_odt>[\-\$\ \d\,\.]+)',
            PRP.INDEX_RE_FLAGS: PRP.FLAG_RETURN_ON_MATCH | PRP.FLAG_ONCE_PER_SECTION,
            PRP.INDEX_RE_TRIGGER_ON: '{total_nsf}',
            PRP.INDEX_RE_TRIGGER_OFF: '{total_odt}'
        },
        'grand_total': {
            PRP.INDEX_RE_STRING:
                r'^Grand\ Total:\s*(?P<grand_total>[\-\$\ \d\,\.]+)',
            PRP.INDEX_RE_FLAGS: PRP.FLAG_RETURN_ON_MATCH | PRP.FLAG_END_OF_SECTION,
            PRP.INDEX_RE_TRIGGER_ON: '{total_odt}',
            PRP.INDEX_RE_TRIGGER_OFF: '{grand_total}'
        }
    }

    expected_value_1 = {'report_id': '', 'file_date': '', 'run_time': '', 'run_date': '', 'fee_type': '', 'tx_seq': '',
                        'trace_num': '',
                        'balance': '', 'tx_date': '', 'tx_amt': '', 'tx_desc': '', 'fee_code': '', 'nsf_fee': '',
                        'ac_type': '',
                        'ac_num': '', 'total_nsf': '', 'total_odt': '', 'grand_total': ''}

    expected_value_2 = ['file_date']

    expected_value_3_1 = ['run_date']
    expected_value_3_2 = {'run_date': '01/01/16', 'run_time': '00:14:18', 'subsection_depth': 0, 'current_subsection_parents': [], 'subsection_line_count': 2}

    expected_value_4_1 = ['tx_line']
    expected_value_4_2 = {'ac_num': '394654', 'ac_type': '54', 'balance': '$     0.00', 'fee_code': '  ',
                          'fee_type': 'ZERO OVERDRAFT FEE     ',
                          'nsf_fee': '$  0.00', 'trace_num': '658524658 ', 'tx_amt': '$     5.41',
                          'tx_date': '01/02/16', 'tx_desc': 'VALLARTA SUPERMARK ARVIN', 'tx_seq': '56546',
                          'subsection_depth': 0, 'current_subsection_parents': [], 'subsection_line_count': 4}

    def test_load_re(self):
        rtp = PyReParse()
        fld_names = rtp.load_re_lines(TestPyReParse.test_re_lines)
        self.assertEqual(TestPyReParse.expected_value_1, fld_names)

    def test_match_1(self):
        rtp = PyReParse()
        fld_names = rtp.load_re_lines(TestPyReParse.test_re_lines)
        self.assertEqual(TestPyReParse.expected_value_1, fld_names)
        match_re_lines, last_captured = rtp.match(TestPyReParse.in_line_0)
        self.assertEqual(['report_id'], match_re_lines)
        match_re_lines, last_captured = rtp.match(TestPyReParse.in_line_1)
        self.assertEqual(TestPyReParse.expected_value_2, match_re_lines)

    def test_match_2(self):
        rtp = PyReParse()
        fld_names = rtp.load_re_lines(TestPyReParse.test_re_lines)
        match_re_lines, last_captured = rtp.match(TestPyReParse.in_line_0)
        match_re_lines, last_captured = rtp.match(TestPyReParse.in_line_1)
        match_re_lines, last_captured = rtp.match(TestPyReParse.in_line_2)
        self.assertEqual(TestPyReParse.expected_value_3_1, match_re_lines)
        self.assertEqual(TestPyReParse.expected_value_3_2, rtp.last_captured_fields)

    def test_match_3(self):

        global cb_txline_cnt, cb_rptid_cnt
        cb_txline_cnt = 0
        cb_rptid_cnt = 0

        PRP = PyReParse
        rtp = PyReParse()
        fld_names = rtp.load_re_lines(TestPyReParse.test_re_lines)

        # Match against line_1
        match_re_lines, last_captured = rtp.match(TestPyReParse.in_line_0)
        # file_date def should have a mach attempt count of 1
        self.assertEqual(1, rtp.re_defs['report_id'][PRP.INDEX_STATES][PRP.INDEX_ST_SECTION_LINES_MATCHED])

        # Match against line_1
        match_re_lines, last_captured = rtp.match(TestPyReParse.in_line_1)
        # file_date def should have a mach attempt count of 1
        self.assertEqual(1, rtp.re_defs['report_id'][PRP.INDEX_STATES][PRP.INDEX_ST_SECTION_LINES_MATCHED])
        self.assertEqual(1, rtp.re_defs['file_date'][PRP.INDEX_STATES][PRP.INDEX_ST_SECTION_LINES_MATCHED])

        # Match against line_2
        match_re_lines, last_captured = rtp.match(TestPyReParse.in_line_2)
        # file_date def should have a mach attempt count of 1
        self.assertEqual(1, rtp.re_defs['report_id'][PRP.INDEX_STATES][PRP.INDEX_ST_SECTION_LINES_MATCHED])
        self.assertEqual(1, rtp.re_defs['file_date'][PRP.INDEX_STATES][PRP.INDEX_ST_SECTION_LINES_MATCHED])
        self.assertEqual(1, rtp.re_defs['run_date'][PRP.INDEX_STATES][PRP.INDEX_ST_SECTION_LINES_MATCHED])

        # Match against line_3
        match_re_lines, last_captured = rtp.match(TestPyReParse.in_line_3)
        self.assertEqual(match_re_lines, ['start_tx_lines'])
        # file_date def should have a mach attempt count of 1
        self.assertEqual(1, rtp.re_defs['report_id'][PRP.INDEX_STATES][PRP.INDEX_ST_SECTION_LINES_MATCHED])
        self.assertEqual(1, rtp.re_defs['file_date'][PRP.INDEX_STATES][PRP.INDEX_ST_SECTION_LINES_MATCHED])
        self.assertEqual(1, rtp.re_defs['run_date'][PRP.INDEX_STATES][PRP.INDEX_ST_SECTION_LINES_MATCHED])
        self.assertEqual(1, rtp.re_defs['start_tx_lines'][PRP.INDEX_STATES][PRP.INDEX_ST_SECTION_LINES_MATCHED])

        # Match against line_4
        match_re_lines, last_captured = rtp.match(TestPyReParse.in_line_4)
        # file_date def should have a mach attempt count of 1
        self.assertEqual(1, rtp.re_defs['report_id'][PRP.INDEX_STATES][PRP.INDEX_ST_SECTION_LINES_MATCHED])
        self.assertEqual(1, rtp.re_defs['file_date'][PRP.INDEX_STATES][PRP.INDEX_ST_SECTION_LINES_MATCHED])
        self.assertEqual(1, rtp.re_defs['run_date'][PRP.INDEX_STATES][PRP.INDEX_ST_SECTION_LINES_MATCHED])
        self.assertEqual(1, rtp.re_defs['start_tx_lines'][PRP.INDEX_STATES][PRP.INDEX_ST_SECTION_LINES_MATCHED])
        self.assertEqual(1, rtp.re_defs['tx_line'][PRP.INDEX_STATES][PRP.INDEX_ST_SECTION_LINES_MATCHED])

        # Should be the same results as test_match_2 (results don't intermingle)
        self.assertEqual(TestPyReParse.expected_value_4_1, match_re_lines)
        self.assertEqual(TestPyReParse.expected_value_4_2, rtp.last_captured_fields)

        # Verify that Callbacks have been called...
        self.assertEqual(1, cb_rptid_cnt)
        self.assertEqual(1, cb_txline_cnt)

    def test_parse_file(self):
        PRP = PyReParse
        rtp = PyReParse()
        fld_names = rtp.load_re_lines(TestPyReParse.test_re_lines)
        report_id = ''
        file_date = ''
        run_date = ''
        run_time = ''
        txn_lines = []
        total_nsf = Decimal('0')
        total_odt = Decimal('0')
        grand_total = Decimal('0')

        global cb_txline_cnt, cb_rptid_cnt
        cb_txline_cnt = 0
        cb_rptid_cnt = 0

        mock_lines = [
            TestPyReParse.in_line_0,
            TestPyReParse.in_line_1,
            TestPyReParse.in_line_2,
            TestPyReParse.in_line_3,
            TestPyReParse.in_line_4
        ]

        for line in mock_lines:
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
                m_flds[fld] = rtp.money2decimal(fld, m_flds[fld])
                fld = 'tx_amt'
                m_flds[fld] = rtp.money2decimal(fld, m_flds[fld])
                fld = 'balance'
                m_flds[fld] = rtp.money2decimal(fld, m_flds[fld])
                txn_lines.append(m_flds)
            elif match_def == ['end_tx_lines']:
                pass
            elif match_def == ['total_nsf']:
                m_flds = matched_fields
                fld = 'total_nsf'
                total_nsf = rtp.money2decimal(fld, m_flds[fld])
            elif match_def == ['total_odt']:
                m_flds = matched_fields
                fld = 'total_odt'
                total_odt = rtp.money2decimal(fld, m_flds[fld])
                self.assertGreaterEqual(Decimal('0'), total_odt)
            elif match_def == ['grand_total']:
                m_flds = matched_fields
                fld = 'grand_total'
                grand_total = rtp.money2decimal(fld, m_flds[fld])

                # Run totals & validations
                nsf_tot = Decimal('0')
                for flds in txn_lines:
                    nsf_tot += flds['nsf_fee']
                self.assertEqual(nsf_tot, grand_total)

                # Reset tx_lines array at end of section...
                txn_lines = []

    def test_decimal_precision(self):
        self.assertEqual(Decimal('0.10') + Decimal('0.20'), Decimal('0.30'))

    def test_subsection_basics(self):
        patterns = {
            'sec_start': {
                self.PRP.INDEX_RE_STRING: r'^(?P<sec>SEC)\s*$',
                self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_NEW_SECTION | self.PRP.FLAG_RETURN_ON_MATCH,
                self.PRP.INDEX_RE_TRIGGER_ON: 'True',
                self.PRP.INDEX_RE_TRIGGER_OFF: 'False'
            },
            'sub_start': {
                self.PRP.INDEX_RE_STRING: r'^(?P<sub>SUB)\s*$',
                self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_NEW_SUBSECTION | self.PRP.FLAG_RETURN_ON_MATCH,
                self.PRP.INDEX_RE_TRIGGER_ON: '{sec_start}',
                self.PRP.INDEX_RE_TRIGGER_OFF: 'False'
            }
        }
        rtp = self.PRP()
        rtp.load_re_lines(patterns)
        m, f = rtp.match('SEC\n')
        self.assertEqual(['sec_start'], m)
        self.assertEqual(1, rtp.section_count)
        self.assertEqual(0, rtp.subsection_depth)
        m, f = rtp.match('SUB\n')
        self.assertEqual(['sub_start'], m)
        self.assertEqual(1, rtp.subsection_depth)
        self.assertEqual(('sub_start',), rtp.get_current_subsection())
        self.assertEqual(1, f['subsection_depth'])
        self.assertEqual(1, f['subsection_line_count'])
        self.assertEqual({
            'depth': 1,
            'parents': ['sub_start'],
            'max_depth': 1,
            'counts': {1: 1}
        }, rtp.get_subsection_info())
        rtp.section_reset()
        self.assertEqual(0, rtp.subsection_depth)

    def test_subsection_triggers(self):
        patterns = {
            'sec_start': {
                self.PRP.INDEX_RE_STRING: r'^(?P<sec>SEC)\s*$',
                self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_NEW_SECTION | self.PRP.FLAG_RETURN_ON_MATCH,
                self.PRP.INDEX_RE_TRIGGER_ON: 'True',
                self.PRP.INDEX_RE_TRIGGER_OFF: 'False'
            },
            'sub_start': {
                self.PRP.INDEX_RE_STRING: r'^(?P<sub>SUB)\s*$',
                self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_NEW_SUBSECTION | self.PRP.FLAG_RETURN_ON_MATCH,
                self.PRP.INDEX_RE_TRIGGER_ON: '{sec_start}',
                self.PRP.INDEX_RE_TRIGGER_OFF: 'False'
            },
            'depth_trigger': {
                self.PRP.INDEX_RE_STRING: r'^(?P<trig>DEPTHTRIG)\s*$',
                self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_RETURN_ON_MATCH,
                self.PRP.INDEX_RE_TRIGGER_ON: '<SUBSECTION_DEPTH> == 1 and {sub_start}',
                self.PRP.INDEX_RE_TRIGGER_OFF: '{depth_trigger}'
            }
        }
        rtp = self.PRP()
        rtp.load_re_lines(patterns)
        m, f = rtp.match('SEC\n')
        self.assertEqual(['sec_start'], m)
        m, f = rtp.match('DEPTHTRIG\n')
        self.assertEqual(None, m)
        m, f = rtp.match('SUB\n')
        self.assertEqual(['sub_start'], m)
        m, f = rtp.match('DEPTHTRIG\n')
        self.assertEqual(['depth_trigger'], m)

    def test_nested_subsections(self):
        patterns = {
            'sec_start': {
                self.PRP.INDEX_RE_STRING: r'^(?P<sec>SEC)\s*$',
                self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_NEW_SECTION | self.PRP.FLAG_RETURN_ON_MATCH,
                self.PRP.INDEX_RE_TRIGGER_ON: 'True',
                self.PRP.INDEX_RE_TRIGGER_OFF: 'False'
            },
            'sub1_start': {
                self.PRP.INDEX_RE_STRING: r'^(?P<sub1>SUB1)\s*$',
                self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_NEW_SUBSECTION | self.PRP.FLAG_RETURN_ON_MATCH,
                self.PRP.INDEX_RE_TRIGGER_ON: '{sec_start}',
                self.PRP.INDEX_RE_TRIGGER_OFF: 'False'
            },
            'sub2_start': {
                self.PRP.INDEX_RE_STRING: r'^(?P<sub2>SUB2)\s*$',
                self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_NEW_SUBSECTION | self.PRP.FLAG_RETURN_ON_MATCH,
                self.PRP.INDEX_RE_TRIGGER_ON: '{sub1_start}',
                self.PRP.INDEX_RE_TRIGGER_OFF: 'False'
            },
            'ender': {
                self.PRP.INDEX_RE_STRING: r'^(?P<end>ENDER)\s*$',
                self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_END_OF_SECTION | self.PRP.FLAG_RETURN_ON_MATCH,
                self.PRP.INDEX_RE_TRIGGER_ON: '{sub2_start}',
                self.PRP.INDEX_RE_TRIGGER_OFF: 'False'
            },
            'ender2': {
                self.PRP.INDEX_RE_STRING: r'^(?P<end2>ENDER2)\s*$',
                self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_END_OF_SECTION | self.PRP.FLAG_RETURN_ON_MATCH,
                self.PRP.INDEX_RE_TRIGGER_ON: 'True',
                self.PRP.INDEX_RE_TRIGGER_OFF: 'False'
            }
        }
        rtp = self.PRP()
        rtp.load_re_lines(patterns)
        m, f = rtp.match('SEC\n')
        self.assertEqual(['sec_start'], m)
        self.assertEqual(1, rtp.section_count)
        self.assertEqual(0, rtp.subsection_depth)
        m, f = rtp.match('SUB1\n')
        self.assertEqual(['sub1_start'], m)
        self.assertEqual(1, rtp.subsection_depth)
        self.assertEqual(('sub1_start',), rtp.get_current_subsection())
        m, f = rtp.match('SUB2\n')
        self.assertEqual(['sub2_start'], m)
        self.assertEqual(2, rtp.subsection_depth)
        self.assertEqual(('sub1_start', 'sub2_start'), rtp.get_current_subsection())
        m, f = rtp.match('ENDER\n')
        self.assertEqual(['ender'], m)
        self.assertEqual(0, rtp.subsection_depth)
        self.assertEqual((), rtp.get_current_subsection())
        m, f = rtp.match('ENDER2\n')
        self.assertEqual(['ender2'], m)
        self.assertEqual(0, rtp.subsection_depth)
        self.assertEqual((), rtp.get_current_subsection())
        self.assertEqual(2, rtp.get_max_subsection_depth())
        self.assertEqual({1: 1, 2: 1}, rtp.get_subsection_depth_counts())

    def test_subsection_reset(self):
        patterns = {
            'sec_start': {
                self.PRP.INDEX_RE_STRING: r'^(?P<sec>SEC)\s*$',
                self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_NEW_SECTION | self.PRP.FLAG_RETURN_ON_MATCH,
                self.PRP.INDEX_RE_TRIGGER_ON: 'True',
                self.PRP.INDEX_RE_TRIGGER_OFF: 'False'
            },
            'sub1_start': {
                self.PRP.INDEX_RE_STRING: r'^(?P<sub1>SUB1)\s*$',
                self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_NEW_SUBSECTION | self.PRP.FLAG_RETURN_ON_MATCH,
                self.PRP.INDEX_RE_TRIGGER_ON: '{sec_start}',
                self.PRP.INDEX_RE_TRIGGER_OFF: 'False'
            },
            'sub2_start': {
                self.PRP.INDEX_RE_STRING: r'^(?P<sub2>SUB2)\s*$',
                self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_NEW_SUBSECTION | self.PRP.FLAG_RETURN_ON_MATCH,
                self.PRP.INDEX_RE_TRIGGER_ON: '{sub1_start}',
                self.PRP.INDEX_RE_TRIGGER_OFF: 'False'
            },
            'ender': {
                self.PRP.INDEX_RE_STRING: r'^(?P<end>ENDER)\s*$',
                self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_END_OF_SECTION | self.PRP.FLAG_RETURN_ON_MATCH,
                self.PRP.INDEX_RE_TRIGGER_ON: '{sub2_start}',
                self.PRP.INDEX_RE_TRIGGER_OFF: 'False'
            }
        }
        rtp = self.PRP()
        rtp.load_re_lines(patterns)
        m, f = rtp.match('SEC\n')
        m, f = rtp.match('SUB1\n')
        m, f = rtp.match('SUB2\n')
        self.assertEqual(2, rtp.subsection_depth)
        m, f = rtp.match('ENDER\n')
        self.assertEqual(0, rtp.subsection_depth)
        self.assertEqual((), rtp.get_current_subsection())
        # NEW_SECTION resets all
        m, f = rtp.match('SEC\n')
        self.assertEqual(0, rtp.subsection_depth)
        self.assertEqual((), rtp.get_current_subsection())
        self.assertEqual(2, rtp.section_count)
        # report_reset clears max/counts
        rtp.report_reset()
        self.assertEqual(0, rtp.get_max_subsection_depth())
        self.assertEqual({}, rtp.get_subsection_depth_counts())

    def test_exposure_methods(self):
        patterns = {
            'sec_start': {
                self.PRP.INDEX_RE_STRING: r'^(?P<sec>SEC)\s*$',
                self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_NEW_SECTION | self.PRP.FLAG_RETURN_ON_MATCH,
                self.PRP.INDEX_RE_TRIGGER_ON: 'True',
                self.PRP.INDEX_RE_TRIGGER_OFF: 'False'
            },
            'sub1_start': {
                self.PRP.INDEX_RE_STRING: r'^(?P<sub1>SUB1)\s*$',
                self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_NEW_SUBSECTION | self.PRP.FLAG_RETURN_ON_MATCH,
                self.PRP.INDEX_RE_TRIGGER_ON: '{sec_start}',
                self.PRP.INDEX_RE_TRIGGER_OFF: 'False'
            },
            'sub2_start': {
                self.PRP.INDEX_RE_STRING: r'^(?P<sub2>SUB2)\s*$',
                self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_NEW_SUBSECTION | self.PRP.FLAG_RETURN_ON_MATCH,
                self.PRP.INDEX_RE_TRIGGER_ON: '{sub1_start}',
                self.PRP.INDEX_RE_TRIGGER_OFF: 'False'
            }
        }
        rtp = self.PRP()
        rtp.load_re_lines(patterns)
        self.assertEqual(0, rtp.get_subsection_depth())
        self.assertEqual((), rtp.get_current_subsection())
        self.assertEqual(0, rtp.get_max_subsection_depth())
        self.assertEqual({}, rtp.get_subsection_depth_counts())
        self.assertEqual({
            'depth': 0,
            'parents': [],
            'max_depth': 0,
            'counts': {}
        }, rtp.get_subsection_info())
        m, f = rtp.match('SEC\n')
        m, f = rtp.match('SUB1\n')
        self.assertEqual(1, rtp.get_subsection_depth())
        self.assertEqual(('sub1_start',), rtp.get_current_subsection())
        self.assertEqual(1, rtp.get_max_subsection_depth())
        self.assertEqual({1: 1}, rtp.get_subsection_depth_counts())
        self.assertEqual({
            'depth': 1,
            'parents': ['sub1_start'],
            'max_depth': 1,
            'counts': {1: 1}
        }, rtp.get_subsection_info())
        m, f = rtp.match('SUB2\n')
        self.assertEqual(2, rtp.get_subsection_depth())
        self.assertEqual(('sub1_start', 'sub2_start'), rtp.get_current_subsection())
        self.assertEqual(2, rtp.get_max_subsection_depth())
        self.assertEqual({1: 1, 2: 1}, rtp.get_subsection_depth_counts())
        self.assertEqual({
            'depth': 2,
            'parents': ['sub1_start', 'sub2_start'],
            'max_depth': 2,
            'counts': {1: 1, 2: 1}
        }, rtp.get_subsection_info())

    def test_error_cases(self):
        # Orphan sub without parent trigger
        orphan_patterns = {
            'orphan_sub': {
                self.PRP.INDEX_RE_STRING: r'^(?P<orphan>SUB)\s*$',
                self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_NEW_SUBSECTION | self.PRP.FLAG_RETURN_ON_MATCH,
                self.PRP.INDEX_RE_TRIGGER_ON: 'True',
                self.PRP.INDEX_RE_TRIGGER_OFF: 'False'
            }
        }
        rtp = self.PRP()
        f = io.StringIO()
        with redirect_stdout(f):
            rtp.load_re_lines(orphan_patterns)
        self.assertIn('Warning: [orphan_sub] has FLAG_NEW_SUBSECTION but TRIGGER_ON "True" lacks {parent_pattern} reference.', f.getvalue())

        # Bad symbol in trigger
        bad_patterns = {
            'bad': {
                self.PRP.INDEX_RE_STRING: r'^(?P<bad>BAD)\s*$',
                self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_RETURN_ON_MATCH,
                self.PRP.INDEX_RE_TRIGGER_ON: '<BAD_SYM> == 1',
                self.PRP.INDEX_RE_TRIGGER_OFF: 'False'
            }
        }
        rtp = self.PRP()
        self.assertRaises(TriggerDefException, rtp.load_re_lines, bad_patterns)

    def test_with_existing(self):
        rtp = self.PRP()
        rtp.load_re_lines(self.test_re_lines)
        for _ in range(10):
            m, f = rtp.match('dummy\n')
            self.assertEqual(None, m)
        self.assertEqual(0, rtp.subsection_depth)
        self.assertEqual(0, rtp.get_subsection_depth())
        self.assertEqual((), rtp.get_current_subsection())
        self.assertEqual(0, rtp.get_max_subsection_depth())
        self.assertEqual({}, rtp.get_subsection_depth_counts())
        # Existing tests should still pass unchanged, as verified by running the suite

    def test_parallel_basic(self):
        # Mock 2-section file
        mock_content = [
            '**SEC1\n', 'data1\n', 'END1\n',
            '**SEC2\n', 'data2\n', 'END2\n'
        ]
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(''.join(mock_content))
            mock_path = f.name

        patterns = {
            'sec': {
                self.PRP.INDEX_RE_STRING: r'^\*\*(?P<id>SEC\d+)\s*$',
                self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_NEW_SECTION | self.PRP.FLAG_RETURN_ON_MATCH,
                self.PRP.INDEX_RE_TRIGGER_ON: 'True'
            },
            'data': {
                self.PRP.INDEX_RE_STRING: r'^data(?P<d>\d+)\s*$',
                self.PRP.INDEX_RE_FLAGS: 0,
                self.PRP.INDEX_RE_TRIGGER_ON: '{sec}'
            },
            'end': {
                self.PRP.INDEX_RE_STRING: r'^END\d+\s*$',
                self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_END_OF_SECTION,
                self.PRP.INDEX_RE_TRIGGER_ON: 'True'
            }
        }

        prp = self.PRP(patterns)

        # Serial
        serial_data = []
        with open(mock_path) as f:
            for line in f:
                m, flds = prp.match(line)
                if m:
                    serial_data.append((m, flds))

        # Parallel
        parallel_sections = prp.parse_file_parallel(mock_path)
        parallel_data = []
        for sec in parallel_sections:
            for item in sec['fields_list']:
                parallel_data.append((item['match_def'], item['fields']))

        self.assertEqual(serial_data, parallel_data)

        os.unlink(mock_path)

    def test_parse_file_real_data(self):
        import tempfile
        import os

        PRP = self.PRP

        patterns = {
            'report_start': {
                PRP.INDEX_RE_STRING: r'^\*\*REPORT(?P<rep_id>\d+)\s*$',
                PRP.INDEX_RE_FLAGS: PRP.FLAG_NEW_SECTION | PRP.FLAG_RETURN_ON_MATCH,
                PRP.INDEX_RE_TRIGGER_ON: 'True'
            },
            'cust_start': {
                PRP.INDEX_RE_STRING: r'^CUSTOMER(?P<cust_id>\d+)\s*$',
                PRP.INDEX_RE_FLAGS: PRP.FLAG_NEW_SUBSECTION | PRP.FLAG_RETURN_ON_MATCH,
                PRP.INDEX_RE_TRIGGER_ON: '{report_start}'
            },
            'tx_line': {
                PRP.INDEX_RE_STRING: r'^TX(?P<tx_id>\d+)\s+(?P<amt>\$[\d,]+\.\d{2}).*',
                PRP.INDEX_RE_TRIGGER_ON: '{cust_start}'
            },
            'cust_total': {
                PRP.INDEX_RE_STRING: r'^TOTAL\s+(?P<total>\$[\d,]+\.\d{2}).*',
                PRP.INDEX_RE_FLAGS: PRP.FLAG_END_OF_SECTION | PRP.FLAG_RETURN_ON_MATCH,
                PRP.INDEX_RE_TRIGGER_ON: '<SUBSECTION_DEPTH> == 1'  # Depth 1 (customer)
            },
            'report_end': {
                PRP.INDEX_RE_STRING: r'^END REPORT\s*$',
                PRP.INDEX_RE_FLAGS: PRP.FLAG_END_OF_SECTION
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            for rep in range(3):
                f.write(f'**REPORT{rep+1}\n')
                for cust in range(1):
                    f.write(f'CUSTOMER{cust+1}\n')
                    for tx in range(100):
                        f.write(f'TX{tx} $1.00\n')
                    f.write('TOTAL $100.00\n')
                f.write('END REPORT\n')
                f.write('\n' * 100)  # Padding
            mock_path = f.name

        prp = self.PRP(patterns)

        sections_serial = prp.parse_file(mock_path)
        self.assertGreaterEqual(len(sections_serial), 3)

        sec0 = sections_serial[0]
        self.assertEqual(sec0['section_start'], 1)

        tx_count = sum(1 for item in sec0['fields_list'] if 'tx_line' in item['match_def'])
        self.assertEqual(tx_count, 100)

        cust_start_count = sum(1 for item in sec0['fields_list'] if 'cust_start' in item['match_def'])
        self.assertEqual(cust_start_count, 1)

        # Check totals
        tx_amts = [prp.money2decimal('amt', item['fields']['amt']) for item in sec0['fields_list'] if 'tx_line' in item['match_def']]
        sec_total = sum(tx_amts)
        cust_total_items = [item for item in sec0['fields_list'] if 'cust_total' in item['match_def']]
        self.assertEqual(len(cust_total_items), 1)
        cust_totals_sum = sum(prp.money2decimal('total', item['fields']['total']) for item in cust_total_items)
        self.assertEqual(cust_totals_sum, sec_total)
        self.assertEqual(Decimal('100.00'), sec_total)  # 100 * $1.00

        # Subs metadata
        sub_items = [item['fields']['current_subsection_parents'] for item in sec0['fields_list'] if 'current_subsection_parents' in item['fields']]
        self.assertTrue(any('cust_start' in parents for parents in sub_items))

        tx_parents = [item['fields']['current_subsection_parents'] for item in sec0['fields_list'] if 'tx_line' in item['match_def']]
        self.assertEqual(len(tx_parents), 100)
        self.assertTrue(all(parents == ['cust_start'] for parents in tx_parents))

        # Parallel equiv
        sections_parallel = prp.parse_file_parallel(mock_path)
        self.assertEqual(sections_serial, sections_parallel)  # Same structure/order

        os.unlink(mock_path)

    def test_parallel_benchmark(self):
        # Use existing test_re_lines, mock large file or skip heavy, assert speedup >1x or time < serial
        pass  # Stub, use time.perf_counter for real

    def test_validate_re_defs_valid(self):
        rtp = self.PRP()
        rtp.load_re_lines(self.test_re_lines)

    def test_validate_re_defs_missing_re_string(self):
        rtp = self.PRP()
        patterns = {'pat': {}}
        with self.assertRaises(ValueError) as cm:
            rtp.load_re_lines(patterns)
        self.assertIn('re_string', str(cm.exception))

    def test_validate_re_defs_bad_flags(self):
        rtp = self.PRP()
        patterns = {'pat': {self.PRP.INDEX_RE_STRING: '...', self.PRP.INDEX_RE_FLAGS: -1}}
        with self.assertRaises(ValueError) as cm:
            rtp.load_re_lines(patterns)
        self.assertIn('flags', str(cm.exception))

    def test_validate_re_defs_bad_trigger_syntax(self):
        rtp = self.PRP()
        patterns = {'pat': {self.PRP.INDEX_RE_STRING: '...', self.PRP.INDEX_RE_TRIGGER_ON: '<BAD_SYM>'}}
        with self.assertRaises(TriggerDefException):
            rtp.load_re_lines(patterns)

    def test_validate_re_defs_trigger_cycle(self):
        rtp = self.PRP()
        patterns = {
            'a': {self.PRP.INDEX_RE_STRING: '^a$', self.PRP.INDEX_RE_TRIGGER_ON: '{b}'},
            'b': {self.PRP.INDEX_RE_STRING: '^b$', self.PRP.INDEX_RE_TRIGGER_ON: '{a}'}
        }
        with self.assertRaises(ValueError) as cm:
            rtp.load_re_lines(patterns)
        self.assertIn('Cycle detected', str(cm.exception))

    def test_validate_re_defs_orphan_subsection(self):
        rtp = self.PRP()
        patterns = {
            'sub': {
                self.PRP.INDEX_RE_STRING: '^sub$',
                self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_NEW_SUBSECTION,
                self.PRP.INDEX_RE_TRIGGER_ON: 'True'
            }
        }
        f = io.StringIO()
        with redirect_stdout(f):
            rtp.load_re_lines(patterns)
        self.assertIn('Warning: [sub] has FLAG_NEW_SUBSECTION but TRIGGER_ON "True" lacks {parent_pattern} reference.', f.getvalue())

    def test_parse_file_stream(self):
        global cb_txline_cnt, cb_rptid_cnt
        cb_txline_cnt = 0
        cb_rptid_cnt = 0

        mock_lines = [
            TestPyReParse.in_line_0 + '\n',
            TestPyReParse.in_line_1 + '\n',
            TestPyReParse.in_line_2 + '\n',
            TestPyReParse.in_line_3 + '\n',
            TestPyReParse.in_line_4 + '\n'
        ]

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.writelines(mock_lines)
            mock_path = f.name

        try:
            rtp = self.PRP()
            rtp.load_re_lines(TestPyReParse.test_re_lines)
            serial_sections = rtp.parse_file(mock_path)

            cb_txline_cnt = 0
            cb_rptid_cnt = 0
            rtp_stream = self.PRP()
            rtp_stream.load_re_lines(TestPyReParse.test_re_lines)

            stream_sections = list(rtp_stream.parse_file_stream(mock_path))
            self.assertEqual(stream_sections, serial_sections)
            self.assertEqual(1, len(stream_sections))
            self.assertEqual(5, len(stream_sections[0]['fields_list']))
            self.assertEqual(1, cb_rptid_cnt)
            self.assertEqual(1, cb_txline_cnt)

            # Test callback
            def mock_sec_cb(sec):
                called.append(sec)

            called = []
            rtp_stream.parse_file_stream(mock_path, callback=mock_sec_cb)
            self.assertEqual(called, serial_sections)
        finally:
            os.unlink(mock_path)

    def test_trigger_perf(self):
        patterns = {
            'abc_pat': {
                self.PRP.INDEX_RE_STRING: r'^ABC(?P<val>\d+)',
                self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_RETURN_ON_MATCH,
                self.PRP.INDEX_RE_TRIGGER_ON: 'True',
                self.PRP.INDEX_RE_TRIGGER_OFF: 'False'
            },
            'def_pat': {
                self.PRP.INDEX_RE_STRING: r'^DEF(?P<val>\d+)',
                self.PRP.INDEX_RE_FLAGS: self.PRP.FLAG_RETURN_ON_MATCH,
                self.PRP.INDEX_RE_TRIGGER_ON: 'True',
                self.PRP.INDEX_RE_TRIGGER_OFF: 'False'
            }
        }
        rtp = self.PRP()
        rtp.load_re_lines(patterns)

        random_lines = ['ABC' + str(i) if i % 2 == 0 else 'DEF' + str(i) for i in range(10000)]
        random.shuffle(random_lines)

        start_time = time.perf_counter()
        for line in random_lines:
            rtp.match(line)
        end_time = time.perf_counter()
        duration = end_time - start_time
        self.assertLess(duration, 1.0, f"Trigger matching took too long: {duration}s")

    def test_stream_matches(self):
        global cb_txline_cnt, cb_rptid_cnt
        cb_txline_cnt = 0
        cb_rptid_cnt = 0

        mock_lines = [
            TestPyReParse.in_line_0 + '\n',
            TestPyReParse.in_line_1 + '\n',
            TestPyReParse.in_line_2 + '\n',
            TestPyReParse.in_line_3 + '\n',
            TestPyReParse.in_line_4 + '\n'
        ]

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.writelines(mock_lines)
            mock_path = f.name

        try:
            rtp_serial = self.PRP()
            rtp_serial.load_re_lines(TestPyReParse.test_re_lines)
            serial_results = []
            for line in mock_lines:
                m, f = rtp_serial.match(line.rstrip('\n'))
                serial_results.append((m, f))

            cb_txline_cnt = 0
            cb_rptid_cnt = 0

            rtp_stream = self.PRP()
            rtp_stream.load_re_lines(TestPyReParse.test_re_lines)
            stream_results = list(rtp_stream.stream_matches(mock_path))

            self.assertEqual(stream_results, serial_results)
            self.assertEqual(1, cb_rptid_cnt)
            self.assertEqual(1, cb_txline_cnt)

            # Test callback
            def mock_cb(m, flds):
                called.append((m, flds))

            called = []
            rtp_stream.stream_matches(mock_path, callback=mock_cb)
            self.assertEqual(called, stream_results)
        finally:
            os.unlink(mock_path)
    
