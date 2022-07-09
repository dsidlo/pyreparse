#!/usr/bin/env python3

import sys
import re
import os
import unittest
import inspect

'''
# TODO: Only hit this regexp between lines A and B of a given Section.
# TODO: Clean up the test data
#       - Scramble AcNumbers
#       - Change or Remove CU references
#       - Restart GitRepo to remove traces of original reports
'''


class PyReParse:

    # RegExp Processing Flags
    FLAG_RETURN_ON_MATCH = 1
    FLAG_RESET_SECTION_LINE = 2
    FLAG_ONCE_PER_SECTION = 4
    FLAG_ONCE_PER_REPORT = 8
    FLAG_END_OF_SECTION = 16

    INDEX_POSITIONAL = 'positional'
    INDEX_RE_STRING = 're_string'
    INDEX_RE_QUICK_CHECK = 're_quick_check'
    INDEX_RE_REGEXP = 'regexp'  # Compiled
    INDEX_RE_TRIGGER_ON = 'trigger_on'
    INDEX_RE_TRIGGER_OFF = 'trigger_off'
    INDEX_RE_STATES = 'states'
    INDEX_RE_FLAGS = 'flags'
    INDEX_RE_REPORT_LINES_MATCHED = 'report_lines_matched'
    INDEX_RE_SECTION_LINES_MATCHED = 'section_lines_matched'
    INDEX_RE_REPORT_MATCH_ATTEMPTS = 'report_match_attempts'
    INDEX_RE_SECTION_MATCH_ATTEMPTS = 'section_match_attempts'
    INDEX_RE_LAST_REPORT_LINE_MATCHED = 'last_report_line_matched'
    INDEX_RE_LAST_SECTION_LINE_MATCHED = 'last_section_line_matched'

    # Trigger strings...
    TRIG_START_REPORT_LINE = '<START_REPORT_LINE>'
    TRIG_END_REPORT_LINE = '<END_REPORT_LINE>'
    TRIG_START_SECTION_LINE = '<START_SECTION_LINE>'
    TRIG_END_SECTION_LINE = '<END_SECTION_LINE>'

    def __init__(self):
        self.re_defs = {}
        self.named_fields = {}
        self.last_captured_fields = {}
        self.re_named_group = re.compile(r'.*\(\?P\<([^\>]+)\>.*', re.MULTILINE | re.DOTALL)
        self.report_line_counter = 0
        self.section_number = 0
        self.section_line_counter = 0
        self.file_name = ''

    def set_file_name(self, file_name):
        self.file_name = file_name

    @staticmethod
    def get_fld_name_re(fld_name):
        return r'\(\?P\<' + fld_name + '\>'

    @staticmethod
    def dict_merge(D1, D2):
        py = {**D1, **D2}
        return py

    def load_re_lines(self, in_hash):
        self.re_defs = {}
        self.named_fields = {}
        return self.append_re_defs(in_hash)

    def append_re_defs(self, in_hash):
        '''
        Load RegularExpressions Hash Structure...

        Loads self.re_defs with the following hash structure...
            're_name': [ r'{regexp w/named groups}', {0 | ReTextReportParserFlag.<flag>}],
            're_name': [ r'{regexp w/named groups}', {0 | ReTextReportParserFlag.<flag>}],
            ...

        Note: The regular expressions in the hash structure will be compiled using the regexp flags
              re.X to allow or the addition of named groups in the form '(?P<fld_name>{regexp}'.
              The field names in the capture groups are used to document in code what fields are
              captured, accessed and manipulated in code, rather that referencing a numeric
              group(1) with an integer index.
              As data is placed into the self.re_def hash, additional elements are added to the
              regexp fld array... including a reference to the compiled regular expression, a counter for
              the number of times the regexp matched, and a place holder for the last line that matched.

        :param in_hash:
            { 're_name_1': [ r'{regexp w/named groups}', {0 | ReTextReportParserFlag.<flag>}],
              're_name_2': [ r'{regexp w/named groups}', {0 | ReTextReportParserFlag.<flag>}],
            ... }

        :return:
            Hash of field names with initial values of ''... see: get_all_fld_names().
            { '{fld_name_1}': ''
              '{fld_name_2}': ''
              ... }
        '''

        rtrpc = PyReParse

        for fld in in_hash:
            # INDEX_RE
            self.re_defs[fld] = in_hash[fld]

            try:
                self.re_defs[fld] = self.dict_merge(self.re_defs[fld],
                                                    {
                                                        rtrpc.INDEX_RE_REGEXP:
                                                            re.compile(in_hash[fld][rtrpc.INDEX_RE_STRING], re.X)
                                                            if rtrpc.INDEX_RE_STRING in in_hash[fld]
                                                            else None,
                                                        rtrpc.INDEX_RE_STATES: {
                                                            rtrpc.INDEX_RE_REPORT_LINES_MATCHED: 0,
                                                            rtrpc.INDEX_RE_SECTION_LINES_MATCHED: 0,
                                                            rtrpc.INDEX_RE_LAST_REPORT_LINE_MATCHED: 0,
                                                            rtrpc.INDEX_RE_LAST_SECTION_LINE_MATCHED: 0,
                                                            rtrpc.INDEX_RE_REPORT_MATCH_ATTEMPTS: 0,
                                                            rtrpc.INDEX_RE_SECTION_MATCH_ATTEMPTS: 0
                                                        }
                                                    })

            except:
                print(f'*** Exception Hit on Compiling Regexp [{fld}]!')
                os.exit(1)


        return self.get_all_fld_names()

    def get_all_fld_names(self):
        rtrpc = PyReParse
        # Get all field_names from all regexps
        for fld in self.re_defs:
            if rtrpc.INDEX_RE_STRING in self.re_defs[fld]:
                # process are regexp...
                restr = self.re_defs[fld][rtrpc.INDEX_RE_STRING]
            else:
                # process positional fields...
                pos_flds = self.re_defs[fld][rtrpc.INDEX_POSITIONAL]
                restr = None

            if restr:
                # Process a regexp...
                while True:
                    ng = self.re_named_group.match(restr, re.MULTILINE | re.DOTALL)
                    if ng is not None:
                        fld_name = ng.group(1)
                        fld_name_expr = self.get_fld_name_re(fld_name)
                        self.named_fields[fld_name] = ''
                        restr = re.sub(fld_name_expr, r'(', restr)
                    else:
                        break
            else:
                # Process positional fields match...
                None

        # TODO: add code to create structures for on/off triggers
        # TODO: add call to self.validate_re_defs()

        return self.named_fields

    def validate_re_defs(self):
        '''
        Validate self.re_defs.

        Called before returning from self.append_re_defs().

        Make sure that each entry has a 're_string' or a 'positional'.
        Ensure that fields in trigger_on and trigger_off exist and make sense.

        :return:
        '''
        pass

    def eval_triggers(self, reg_def):
        '''
        This version of eval_triggers only expect a single re_def-name within a trigger and nothing more.
        A return value of True means that a match should be performed against the defined regexo.

        :param reg_def:
        :return:
        '''

        rtrpc = PyReParse
        redef_name = reg_def[rtrpc.INDEX_RE_TRIGGER_ON]
        if redef_name == '':
            trig_on_state = True
        else:
            if self.re_defs[redef_name][rtrpc.INDEX_RE_STATES][rtrpc.INDEX_RE_SECTION_LINES_MATCHED] > 0:
                trig_on_state = True
            else:
                trig_on_state = False

        redef_name = reg_def[rtrpc.INDEX_RE_TRIGGER_OFF]
        if redef_name == '':
            trig_off_state = False
        else:
            if self.re_defs[redef_name][rtrpc.INDEX_RE_STATES][rtrpc.INDEX_RE_SECTION_LINES_MATCHED] > 0:
                trig_off_state = True
            else:
                trig_off_state = False

        if trig_on_state:
            if trig_off_state:
                return False
            else:
                return True
        else:
            return False


    def _eval_triggers(self, reg_def):
        """
        Process trigger_on and trigger_off properties.
        If trigger_on result is true, then we turn on regexp processing for the re_def.
        If trigger_off result is true, then we turn off regexp processing for the re_def.
        trigger_off superceeds trigger_on

        :param reg_def:
        :return:
        """

        # Started writing new logic...

        # Check trigger_on...
        # Valid Symbols in Trigger_on:
        # - Any re_defs field name
        #   - Only perform match after <re_fld_name> has matched.
        # - <Report_Start_line>[n]
        #   - Start running match once Report-Line [n] is hit
        # - <Section_Stat_Line>[n]
        #   - Start running match once Section-Line [n] is hit
        trigger_on = reg_def[rtrpc.INDEX_RE_TRIGGER_ON]
        curr_bool_oper = ''
        curr_state = False
        trigger_on_state = False
        while True:
            # Check for a <symbol> re_def-name
            m = re.match(r'(\s*([^\|\&]+)\s*)(?:[\|\&\ ]+)', trigger_on, re.X)
            rm_pat = m.group(1)
            sym_or_name = m.group(2)
            if sym_or_name:
                # Process symbol or re_def-name
                # Remove the symbol or name just processed
                if curr_bool_oper == False:
                    if sym_or_name[0] == '<':
                        curr_sate = self.get_symbolic_state(sym_or_name)
                    else:
                        if self.re_defs[sym_or_name][rtrpc.INDEX_RE_STATES][rtrpc.INDEX_RE_LAST_SECTION_LINE_MATCHED] > 0:
                            curr_state = True
                        else:
                            curr_state = False
                pass
                trigger_on = re.sub(f'^{rm_pat}', '', trigger_on)

            m = re.match(r'(\s*([\|\&]{1}\s*)(?:\s*[^\|\&\ ]+))', trigger_on, re.X)
            rm_pat = m.group(1)
            next_oper = m.group(2)

            # ... Older logic below...

            # Do was have any operators in the trigger.
            # Operators must only exist between symbols and re_defs.
            # So, operators should not be at the start or the end of a trigger.
            found_oper = re.match(r'^\s*([\|]|[\&])', trigger_on)

            if found_oper:
                # Pull next <symbol|field> + <operator>
                m = re.match(r'([^\|\&]+)(?:[\|\&]*)', trigger_on)
                if m:
                    # Get the current trigger...
                    trig_mch = m.group(0)
                    trig_nam = m.group(1)
                    trig_opr = m.group(2)
                    tcomp = re.match('(\<[^\>]+\>)\[(\d+)\]', trig_nam)
                    if tcomp:
                        # Trig is a special variable...
                        tmatch = tcomp.group(0)
                        tsymbol = tcomp.group(1)
                        tval = tcomp.group(2)
                        # Calculate trigger state...
                        _state = self.get_symbolic_state(tsymbol, tval)
                        if cur_operator == '|':
                            trigger_on_state = trigger_on_state or _state
                        elif cur_operator == '&':
                            trigger_on_state = trigger_on_state and _state
                    else:
                        # Trig is re_def...
                        if self.re_defs[trig_nam][rtrpc.INDEX_RE_STATES][rtrpc.INDEX_RE_SECTION_LINES_MATCHED] > 0:
                            _state = True
                        else:
                            _state = False
                        # Calculate the current state...
                        if cur_operator == '|':
                            trigger_on_state = trigger_on_state or _state
                        elif cur_operator == '&':
                            trigger_on_state = trigger_on_state and _state

                    cur_operator = trig_opr

        # Check trigger_off...
        # - Any re_defs field name
        #   - Stop matching after <re_fld_name> has matched.
        # - <Report_End_line>[n]
        #   - Stop running match once Report-Line [n] is hit
        # - <Section_Stat_Line>[n]
        #   - Stop running match once Section-Line [n] is hit
        trigger_off = reg_def[rtrpc.INDEX_RE_TRIGGER_OFF]
        cur_operator = ''
        trigger_off_state = FALSE
        while TRUE:
            found_oper = re.match(r'([\|]|[\&])', trigger_on)
            if found_oper:
                m = re.match(r'([^\|\&]+)[\|\&]', trigger_on)
                if m:
                    # Get the current trigger...
                    trig_mch = m.group(0)
                    trig_nam = m.group(1)
                    trig_opr = m.group(2)
                    tcomp = re.match('(\<[^\>]+\>)\[(\d+)\]', trig_nam)
                    if tcomp:
                        # Trig is a special variable...
                        tmatch = tcomp.group(0)
                        tsymbol = tcomp.group(1)
                        tval = tcomp.group(2)
                        # Calculate trigger state...
                        _state = get_symbolic_state(tsymbol, tval)
                        if cur_operator == '|':
                            trigger_off_state = trigger_off_state or _state
                        elif cur_operator == '&':
                            trigger_off_state = trigger_off_state and _state
                    else:
                        # Trig is re_def...
                        if self.re_defs[trig_nam][rtrpc.INDEX_RE_STATES][rtrpc.INDEX_RE_SECTION_LINES_MATCHED] > 0:
                            _state = True
                        else:
                            _state = False
                        # Calculate the current state...
                        if cur_operator == '|':
                            trigger_off_state = trigger_off_state or _state
                        elif cur_operator == '&':
                            trigger_off_state = trigger_off_state and _state

                    cur_operator = trig_opr

        if trigger_on_state is False and trigger_off_state is False:
            return False

        if trigger_on_state is True and trigger_off_state is False:
                return True
        if trigger_off_state:
            return True

        final_state = trigger_on_state

    def get_symbolic_state(self, symbol, value):
        '''
        Given a symbol and value such as {START_SECTION_LINE}[3]

        :param symbol:
        :param value:
        :return:
        '''
        rtrpc = PyReParse
        if symbol == rtrpc.TRIG_START_REPORT_LINE:
            return self.report_line_counter >= int(value)
        elif symbol == rtrpc.TRIG_END_REPORT_LINE:
            return self.report_line_counter >= int(value)
        elif symbol == rtrpc.TRIG_START_SECTIOM_LINE:
            return self.report_line_counter >= int(value)
        elif symbol == rtrpc.TRIG_END_SECTION_LINE:
            return self.report_line_counter >= int(value)

    def match(self, in_line, debug=False, limit_matches=None):
        '''
        Given a text input line, check if any of our regexp(s) match to it.

        If we have a line specific patterns, and the current line is equal to one of them, we do try to
        match to that line-specific-match immediately. And return immediately if the regexp line
        includes the RETURN_ON_MATCH flag...

        Otherwise, we execute regexp matches against against all line-non-specific regexps in our input list.
        If any regular expressions from our input list match the line, their names are returned as a list.

        :param in_line:
        :param line_count:
        :return:
        '''
        rtrpc = PyReParse
        # Increment total report and page line counters
        self.report_line_counter += 1
        if limit_matches:
            if limit_matches <= self.report_line_counter:
                print(f'*** Exiting: limit_matches is set to [{limit_matches}]')
                sys.exit(1)
        self.section_number += 1
        self.section_line_counter += 1
        # Initialize matched Def list (returned value)
        matched_defs = None
        # Initialize dict of last fields captured.
        self.last_captured_fields = {}
        # dict for adding an increment value to fld names that are already in the
        # last captured dictionary.
        # We should not see <field_name>-<n> values in the last_captured dictionary.
        # If we do, we know that we have either duplicate field names in our regexp defs or
        # we have some other problem with the way we are using the parser.
        fn_inc = {}
        if debug:
            print(f'match: line[{in_line}]')
        for fld in self.re_defs:
            # Check if match should be triggered.
            # Triggers returning true means skip match evaluation,
            # if True:
            if debug:
                print(f'regexp: [{fld}]')
            if self.eval_triggers(self.re_defs[fld]):
                if debug:
                    print(f'--- Triggered[{fld}]...')
                if self.re_defs[fld][rtrpc.INDEX_RE_REGEXP] is None:
                    continue
                m = self.re_defs[fld][rtrpc.INDEX_RE_REGEXP].match(in_line)
                self.re_defs[fld][rtrpc.INDEX_RE_STATES][rtrpc.INDEX_RE_REPORT_MATCH_ATTEMPTS] += 1
                self.re_defs[fld][rtrpc.INDEX_RE_STATES][rtrpc.INDEX_RE_SECTION_MATCH_ATTEMPTS] += 1
                if m:
                    if debug:
                        print(f'--- *** Matched[{fld}] ***')
                    # If we get a match, place values from captured groups (by name) into
                    # the self.named_field dictionary (by field name).
                    for fn in m.re.groupindex:
                        self.named_fields[fn] = m.group(fn)
                    for fn in m.re.groupindex:
                        if fn in self.last_captured_fields:
                            if fn in fn_inc:
                                fn_inc[fn] += 1
                            else:
                                fn_inc[fn] = 1
                            # We've added a increment value to the fld name, if it already exists in the dict.
                            self.last_captured_fields[f'{fn}-<{fn_inc[fn]}>'] = m.group(fn)
                        else:
                            self.last_captured_fields[fn] = m.group(fn)
                    # Update status values of our regexps lines in the re_defs dict...
                    self.re_defs[fld][rtrpc.INDEX_RE_STATES][rtrpc.INDEX_RE_REPORT_LINES_MATCHED] += 1
                    self.re_defs[fld][rtrpc.INDEX_RE_STATES][rtrpc.INDEX_RE_SECTION_LINES_MATCHED] += 1
                    self.re_defs[fld][rtrpc.INDEX_RE_STATES][
                        rtrpc.INDEX_RE_LAST_REPORT_LINE_MATCHED] = self.report_line_counter
                    self.re_defs[fld][rtrpc.INDEX_RE_STATES][
                        rtrpc.INDEX_RE_LAST_SECTION_LINE_MATCHED] = self.section_line_counter
                    if matched_defs is None:
                        matched_defs = []
                    # Capture the list of re_defs entries that match this line.
                    matched_defs.append(fld)
                    # Perform FLAG operations...
                    if self.re_defs[fld][rtrpc.INDEX_RE_FLAGS] & rtrpc.FLAG_RESET_SECTION_LINE:
                        # Increment the section counter...
                        self.section_number += 1
                        # Reset sectional flags and counters...
                        self.section_reset()
                        # Fields that reset sections also match atleast once within those sections...
                        self.re_defs[fld][rtrpc.INDEX_RE_STATES][rtrpc.INDEX_RE_SECTION_MATCH_ATTEMPTS] = 1
                        self.re_defs[fld][rtrpc.INDEX_RE_STATES][rtrpc.INDEX_RE_SECTION_LINES_MATCHED] = 1
                        self.re_defs[fld][rtrpc.INDEX_RE_STATES][rtrpc.INDEX_RE_LAST_SECTION_LINE_MATCHED] = 1
                    if self.re_defs[fld][rtrpc.INDEX_RE_FLAGS] & rtrpc.FLAG_END_OF_SECTION:
                        # Reset sectional flags and counters...
                        self.section_reset()

                    if self.re_defs[fld][rtrpc.INDEX_RE_FLAGS] | rtrpc.FLAG_RETURN_ON_MATCH:
                        return matched_defs, self.last_captured_fields

                else:
                    # RegExp fld did not match...
                    # Check for optional ReQuickCheck field...
                    if rtrpc.INDEX_RE_QUICK_CHECK in self.re_defs[fld]:
                        # Do we have a QuickCheck Entry? Yes, Do a quick check...
                        line_no_lf = re.sub(r"\n", r"", in_line)
                        if re.match(self.re_defs[fld][rtrpc.INDEX_RE_QUICK_CHECK], in_line, re.X):
                            print(f'\n*** A RegExp [{fld}] may have missed a line in File[{self.file_name}] at...')
                            print(f'   Line [{line_no_lf}]')
                            print(f'   Report Line [{self.report_line_counter}]')
                            print(f'   Section Number [{self.section_number}]')
                            print(f'   Section Line [{self.section_line_counter}]')

        # TODO: Add code to check for duplicate fields found (throw error or warning)

        # Return the list of entries in the re_defs dict that match this line.
        return matched_defs, self.last_captured_fields

    def section_reset(self):
        rtrpc = PyReParse
        for fld in self.re_defs:
            self.re_defs[fld][rtrpc.INDEX_RE_STATES][rtrpc.INDEX_RE_SECTION_MATCH_ATTEMPTS] = 0
            self.re_defs[fld][rtrpc.INDEX_RE_STATES][rtrpc.INDEX_RE_SECTION_LINES_MATCHED] = 0
            self.re_defs[fld][rtrpc.INDEX_RE_STATES][rtrpc.INDEX_RE_LAST_SECTION_LINE_MATCHED] = 0

    def money2float(self, fld, in_str):
        re_str = re.sub('[\,\s\$]', '', in_str)
        try:
            ret_val = float(re_str)
        except:
            print(f'*** Exception: Failed to convert string to float [{in_str}] -> [{re_str}]')
            print(f'    Field [field] Report Line [{self.report_line_counter}] ',
                  f'Section Number [{self.section_number}] ',
                  f'Section Line [{self.section_line_counter}]')

        return ret_val

