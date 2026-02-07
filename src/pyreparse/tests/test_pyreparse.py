#!/usr/bin/env python3

import unittest
from pyreparse import PyReParse
from decimal import Decimal

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
            PRP.INDEX_RE_STRING:
                r'''
                ^IPPOSFEE\s+
                FILE\ DATE:\s+(?P<file_date>[\d\/]+)
                ''',
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
            PRP.INDEX_RE_STRING:
                r'''
                ^RUN\ DATE\:\s+(?P<run_date>[\d\/]+)\s+
                RUN\ TIME\:\s+(?P<run_time>[\d\:]+)
                ''',
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
    expected_value_3_2 = {'run_date': '01/01/16', 'run_time': '00:14:18'}

    expected_value_4_1 = ['tx_line']
    expected_value_4_2 = {'ac_num': '394654', 'ac_type': '54', 'balance': '$     0.00', 'fee_code': '  ',
                          'fee_type': 'ZERO OVERDRAFT FEE     ',
                          'nsf_fee': '$  0.00', 'trace_num': '658524658 ', 'tx_amt': '$     5.41',
                          'tx_date': '01/02/16', 'tx_desc': 'VALLARTA SUPERMARK ARVIN', 'tx_seq': '56546'}

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

        global cb_txline_cnt
        cb_txline_cnt = cb_txline_cnt

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
        self.assertEqual(3, cb_rptid_cnt)
        self.assertEqual(1, cb_txline_cnt)

    def test_parse_file(self):
        file_path = 'data/NsfPosFees/999-063217-XXXX-PAID-NSF POS FEES CHARGED page 0001 to 0188.TXT'
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