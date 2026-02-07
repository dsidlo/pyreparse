#!/usr/bin/env python3

import sys
import re
import ast
from decimal import Decimal
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple, Dict, Any

'''

# TODO: add call to self.validate_re_defs()

'''


class TriggerDefException(Exception):
    pass


class PyReParse:
    # RegExp Processing Flags
    FLAG_RETURN_ON_MATCH = 1
    FLAG_NEW_SECTION = 2        # Counters start at 1
    FLAG_ONCE_PER_SECTION = 4
    FLAG_ONCE_PER_REPORT = 8
    FLAG_END_OF_SECTION = 16    # Counters are set to 0
    FLAG_NEW_SUBSECTION = 32    # Start a subsection (nested under current section/parent)

    special_escape_followers = set('aAbBdDFfNnPpRrSsTtVvWwXxZz0123456789')

    KNOWN_FLAGS_MASK = (FLAG_RETURN_ON_MATCH | FLAG_NEW_SECTION | FLAG_ONCE_PER_SECTION | FLAG_ONCE_PER_REPORT |
                        FLAG_END_OF_SECTION | FLAG_NEW_SUBSECTION)

    INDEX_RE_STRING = 're_string'
    INDEX_RE_FLAGS = 'flags'
    INDEX_RE_QUICK_CHECK = 're_quick_check'
    INDEX_RE_REGEXP = 'regexp'                       # Compiled
    INDEX_RE_TRIGGER_ON = 'trigger_on'               # Entry - Trigger_On Assigned by User
    INDEX_RE_TRIGGER_OFF = 'trigger_off'             # Entry - Trigger_Off Assigned by User
    INDEX_RE_TRIGGER_ON_FUNC = 'trigger_on_func'     # Entry - Trigger_On Func Compiled by PyReParse
    INDEX_RE_TRIGGER_OFF_FUNC = 'trigger_off_func'   # Entry - Trigger_Off Func Compiled by PyReParse
    INDEX_RE_TRIGGER_ON_TEXT = 'trigger_on_text'     # Entry - Trigger_On Text Created by PyReParse
    INDEX_RE_TRIGGER_OFF_TEXT = 'trigger_off_text'   # Entry - Trigger_OFF Text Created by PyReParse

    INDEX_RE_CALLBACK = 'callback'  # Entry containing a patterns assigned callback.

    INDEX_STATES = 'states'  # Dict of a patterns states.
    INDEX_ST_REPORT_LINES_MATCHED = 'report_lines_matched'
    INDEX_ST_SECTION_LINES_MATCHED = 'section_lines_matched'
    INDEX_ST_REPORT_MATCH_ATTEMPTS = 'report_match_attempts'
    INDEX_ST_SECTION_MATCH_ATTEMPTS = 'section_match_attempts'
    INDEX_ST_LAST_REPORT_LINE_MATCHED = 'last_report_line_matched'
    INDEX_ST_LAST_SECTION_LINE_MATCHED = 'last_section_line_matched'

    # Subsection Indices
    INDEX_SUBSECTION_DEPTH = 'subsection_depth'
    INDEX_SUBSECTION_PARENTS = 'subsection_parents'
    INDEX_SUBSECTION_LINE_COUNT = 'subsection_line_count'
    INDEX_MAX_SUBSECTION_DEPTH = 'max_subsection_depth'
    INDEX_SUBSECTION_DEPTH_COUNTS = 'subsection_depth_counts'

    # Trigger strings...
    TRIG_SYM_REPORT_LINE = '<REPORT_LINE>'
    TRIG_SYM_SECTION_COUNT = '<SECTION_COUNT>'
    TRIG_SYM_SECTION_LINE = '<SECTION_LINE>'

    # Subsection Trigger Symbols
    TRIG_SYM_SUBSECTION_DEPTH = '<SUBSECTION_DEPTH>'
    TRIG_SYM_SUBSECTION_LINE = '<SUBSECTION_LINE>'

    def __init__(self, regexp_pats=None):
        self.re_defs = {}
        self.all_named_fields = {}
        self.last_captured_fields = {}
        self.re_named_group = re.compile(r'.*\(\?P\<([^\>]+)\>.*', re.X | re.MULTILINE | re.DOTALL)
        self.report_line_count = 0
        self.section_count = 0
        self.section_line_count = 0
        self.file_name = ''
        self.subsection_depth = 0
        self.current_subsection_parents = []
        self.subsection_line_count = 0
        self.max_subsection_depth = 0
        self.subsection_depth_counts = defaultdict(int)
        if regexp_pats is not None:
            self.load_re_lines(regexp_pats)

    def validate_re_defs(self, patterns) -> None:
        """
        Validate the patterns data structure before loading.

        Raises ValueError or TriggerDefException for invalid configurations.
        """
        prp = PyReParse
        known_mask = prp.KNOWN_FLAGS_MASK

        # Validate basic structure
        for pat_name, pat_def in patterns.items():
            if prp.INDEX_RE_STRING not in pat_def:
                raise ValueError(f"Pattern '{pat_name}' missing required '{prp.INDEX_RE_STRING}' key.")
            re_str = pat_def[prp.INDEX_RE_STRING]
            if not isinstance(re_str, str) or len(re_str.strip()) == 0:
                raise ValueError(f"Pattern '{pat_name}' '{prp.INDEX_RE_STRING}' must be a non-empty string.")

            # Validate flags
            if prp.INDEX_RE_FLAGS in pat_def:
                flags = pat_def[prp.INDEX_RE_FLAGS]
                if not isinstance(flags, int) or flags < 0:
                    raise ValueError(f"Pattern '{pat_name}' '{prp.INDEX_RE_FLAGS}' must be a non-negative integer.")
                if flags & ~known_mask != 0:
                    raise ValueError(f"Pattern '{pat_name}' contains unknown flags: {flags & ~known_mask}")

            # Validate triggers syntax
            for trigger_key in [prp.INDEX_RE_TRIGGER_ON, prp.INDEX_RE_TRIGGER_OFF]:
                if trigger_key in pat_def:
                    trigger_text = pat_def[trigger_key]
                    if not isinstance(trigger_text, str):
                        raise ValueError(f"Pattern '{pat_name}' '{trigger_key}' must be a string.")

                    # Simulate replacement for AST parsing
                    func_body = trigger_text
                    while True:
                        m = re.match(r'.*((\<([^\>]+)\>)|(\{([^\}]+)\})).*', func_body, re.MULTILINE | re.DOTALL)
                        if m is None:
                            break
                        elif m.group(2) is not None:
                            # Variable
                            var_name = m.group(2)
                            if var_name == prp.TRIG_SYM_REPORT_LINE:
                                func_body = func_body.replace(var_name, 'prp_inst.report_line_count')
                            elif var_name == prp.TRIG_SYM_SECTION_COUNT:
                                func_body = func_body.replace(var_name, 'prp_inst.section_count')
                            elif var_name == prp.TRIG_SYM_SECTION_LINE:
                                func_body = func_body.replace(var_name, 'prp_inst.section_line_count')
                            elif var_name == prp.TRIG_SYM_SUBSECTION_DEPTH:
                                func_body = func_body.replace(var_name, 'prp_inst.subsection_depth')
                            elif var_name == prp.TRIG_SYM_SUBSECTION_LINE:
                                func_body = func_body.replace(var_name, 'prp_inst.subsection_line_count')
                            else:
                                raise TriggerDefException(f"Unknown variable in '{pat_name}' '{trigger_key}': {m.group(0)}")
                        elif m.group(5) is not None:
                            # Pattern name
                            pn = m.group(5)
                            if pn not in patterns:
                                raise TriggerDefException(f"Unknown pattern reference in '{pat_name}' '{trigger_key}': {pn}")
                            func_body = func_body.replace(m.group(4),
                                                          f"(prp_inst.re_defs['{pn}'][prp.INDEX_STATES][prp.INDEX_ST_SECTION_LINES_MATCHED] > 0)")

                    # AST parse the body
                    func_text = f"def dummy(prp_inst, pat_name): return {func_body}"
                    try:
                        ast.parse(func_text)
                    except SyntaxError as e:
                        raise TriggerDefException(f"Syntax error in '{pat_name}' '{trigger_key}': {e}")

            # Validate NEW_SUBSECTION has parent trigger
            if prp.INDEX_RE_FLAGS in pat_def:
                flags = pat_def[prp.INDEX_RE_FLAGS]
                if flags & prp.FLAG_NEW_SUBSECTION:
                    trigger_on = pat_def.get(prp.INDEX_RE_TRIGGER_ON, '')
                    if '{' not in trigger_on:
                        print(f"Warning: [{pat_name}] has FLAG_NEW_SUBSECTION but TRIGGER_ON \"{trigger_on}\" lacks {{parent_pattern}} reference.")

        # Build dependency graph for cycle detection
        graph = {pat_name: [] for pat_name in patterns}
        for pat_name, pat_def in patterns.items():
            trigger_key = prp.INDEX_RE_TRIGGER_ON
            if trigger_key in pat_def:
                trigger_text = pat_def[trigger_key]
                refs = re.findall(r'\{([^\}]+)\}', trigger_text)
                for ref in refs:
                    if ref in patterns and ref != pat_name:
                        graph[pat_name].append(ref)

        # DFS for cycle detection
        visited = set()
        rec_stack = set()

        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            for neighbor in graph[node]:
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.remove(node)
            return False

        for node in graph:
            if node not in visited:
                if has_cycle(node):
                    raise ValueError(f"Cycle detected in trigger dependencies involving '{node}'")

    def set_file_name(self, file_name):
        self.file_name = file_name

    @staticmethod
    def __gen_fld_name_re(fld_name):
        '''
        A static function to get te generate a regexp string for pulling the
        field/group name from an existing regexp.
        :param fld_name:
        :return:
        '''
        return r'\(\?P\<' + fld_name + r'\>'

    @staticmethod
    def dict_merge(D1, D2):
        '''
        A static unction for merging dictionaries.
        :param D1:
        :param D2:
        :return:
        '''
        py = {**D1, **D2}
        return py

    def load_re_lines(self, in_hash):
        """
        Load a PyReParse regexps data structure into this PyRePrase instance.

        :param in_hash:
        :return:

        The PyReParse regexp data structure...

        <PyReParse_Data-Structure_Name>> =
                {
                    '<regexp_name>': {
                        PRP.INDEX_RE_STRING: r'''<regular expression with named capture groups>''',
                        PRP.INDEX_RE_FLAGS: <PyReParse Flags (or'ed together with '|')>
                        PRP.INDEX_RE_TRIGGER_ON: '<Trigger-On Logic>',
                        PRP.INDEX_RE_TRIGGER_OFF: '<Trigger-Off Logic>',
                        PRP.INDEX_RE_CALLBACK: <Function Reference to Callback>,
                    },
                    ...
                )

        """
        self.validate_re_defs(in_hash)
        self.raw_patterns = in_hash.copy()
        self.re_defs = {}
        self.all_named_fields = {}
        return self.__append_re_defs(in_hash)

    def __create_trigger(self, pat_name, trigger_name):
        '''
        Validate and Compile a pattern's trigger.

        There are 2 trigger types in PyReParse:
          - trigger_on:   When True, causes a match to execute on the given pattern.
          - trigger_off:  When True, causes matching on a pattern to turn off.

        The trigger is a string that evaluates to True or False.
        The trigger string is compiled into a static function, whose referenced in stored into the re_defs data
        structure. The trigger_on and trigger off functions are then called. For match operations to be called on the
        named pattern, the patterns trigger_on must return True while trigger_off returns false, or
        (trigger_on and not trigger_off).
        The string is wrapped into a function with the following parameters:
          - prp_inst: A PyReParse instance
          - pat_name: Name of the regexp pattern in the re_defs data structure.

        An Example: INDEX_RE_TRIGGER_ON: (<REPORT_LINE> >= 2) and [start_tx_lines]
          - "<REPORT_LINE>" is converted to "prp_inst.report_line_count"
          - "[start_tx_lines]" is converted to
            "(prp_inst.re_defs['start_tx_lines'][INDEX_STATES][INDEX_ST_SECTION_LINES_MATCHED] > 0)"

        Counter Variables available:
          - <REPORT_LINE>
          - <SECTION_COUNT>
          - <SECTION_LINE>

        When you reference a pattern-name using brackets '[]', it is tested to see if a match on it has already
        occurred.
          - [report_id]
          - [run_date]
          - [tx_line]

        And the following function is created:
            def trigger_on_start_tx_lines(prp_inst, pat_name):
                return (prp_inst.report_line_count >= 2) and \
                       (prp_inst.re_defs['start_tx_lines'][INDEX_STATES][INDEX_ST_SECTION_LINES_MATCHED] > 0)

        self.report_line_count = 0
        self.section_count = 0
        self.section_line_count = 0

        :param pat_name:
        :param trigger_name:
        :return:
        '''

        # Dynamic trigger function definition
        # This is our function template.
        def_str = """
def <trig_func_name>(prp_inst, pat_name, trigger_name):
    PRP = PyReParse
    return <func_body>
        """

        prp = PyReParse

        # Create a unique name for the function.
        func_name = trigger_name + '_' + pat_name
        func_name = re.sub(r'[^\w\_]', r'_', func_name)
        func_def = def_str.replace('<trig_func_name>', func_name)
        func_body = self.re_defs[pat_name][trigger_name]
        while True:
            '''
            Convert <Variables> into compilable variables.
            Convert [PatternNames] into tests to see if patter names have been hit.
            '''
            m = re.match(r'.*((\<([^\>]+)\>)|(\{([^\}]+)\})).*', func_body, re.MULTILINE | re.DOTALL)
            if m is None:
                break
            elif m and (m.group(2) is not None):
                # We have a variable...
                var_name = m.group(2)
                if var_name == prp.TRIG_SYM_REPORT_LINE:
                    func_body = func_body.replace(var_name, 'prp_inst.report_line_count')
                elif var_name == prp.TRIG_SYM_SECTION_COUNT:
                    func_body = func_body.replace(var_name, 'prp_inst.section_count')
                elif var_name == prp.TRIG_SYM_SECTION_LINE:
                    func_body = func_body.replace(var_name, 'prp_inst.section_line_count')
                elif var_name == prp.TRIG_SYM_SUBSECTION_DEPTH:
                    func_body = func_body.replace(var_name, 'prp_inst.subsection_depth')
                elif var_name == prp.TRIG_SYM_SUBSECTION_LINE:
                    func_body = func_body.replace(var_name, 'prp_inst.subsection_line_count')
                else:
                    raise TriggerDefException(f'Unknown variable: {m.group(0)}')

            elif m and (m.group(5) is not None):
                # We have a pattern-name...
                pn = m.group(5)
                if pn in self.re_defs:
                    func_body = func_body.replace(m.group(4),
                                                  '(prp_inst.re_defs[' + "'" + pn + "'" +
                                                  '][PRP.INDEX_STATES][PRP.INDEX_ST_SECTION_LINES_MATCHED] > 0)')
                else:
                    raise TriggerDefException(f'Unknown pattern-name: {pn}')

        # Create a python function expression...
        func_text = re.sub(r'<func_body>', func_body, func_def)
        # Run the function expression through an AST to validate it.
        # Bad expressions will throw an exception.
        try:
            ast_tree = ast.parse(func_text)
        except SyntaxError as e:
            raise SyntaxError(f"Syntax error in trigger '{trigger_name}' for pattern '{pat_name}': {e}")
        # Yea... Don't execute PyReparse scripts from just anyone.
        # Consider that the PyReparse
        # Execute the function
        exec(func_text)

        # Get a reference to the function that we just created.
        compiled_func = locals()[func_name]

        return compiled_func, func_text

    def __append_re_defs(self, in_hash):
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
        comped_re = None

        for fld in in_hash:
            # INDEX_RE
            self.re_defs[fld] = in_hash[fld]

            # Verify that the regexp compiles...
            comped_re = None
            try:
                raw_pat = in_hash[fld][rtrpc.INDEX_RE_STRING]
                comped_re = re.compile(raw_pat, re.X)
            except re.error as e:
                raise ValueError(f"Failed to compile regex for pattern '{fld}': {e}")
            except Exception as e:
                raise ValueError(f"Unexpected error for pattern '{fld}': {e}")

            # Place the named regexp pattern into the data structure of named pattterns...
            self.re_defs[fld] = self.dict_merge(self.re_defs[fld],
                                                {
                                                    rtrpc.INDEX_RE_REGEXP:
                                                        comped_re
                                                        if rtrpc.INDEX_RE_STRING in in_hash[fld]
                                                        else None,
                                                    rtrpc.INDEX_STATES: {
                                                        rtrpc.INDEX_ST_REPORT_LINES_MATCHED: 0,
                                                        rtrpc.INDEX_ST_SECTION_LINES_MATCHED: 0,
                                                        rtrpc.INDEX_ST_LAST_REPORT_LINE_MATCHED: 0,
                                                        rtrpc.INDEX_ST_LAST_SECTION_LINE_MATCHED: 0,
                                                        rtrpc.INDEX_ST_REPORT_MATCH_ATTEMPTS: 0,
                                                        rtrpc.INDEX_ST_SECTION_MATCH_ATTEMPTS: 0
                                                    }
                                                })

        # Compile Triggers once all fields are in te re_defs data structure...
        for fld in self.re_defs:
            ''' Compile trigger_on...
            Take the trigger strings and compile them into static functions...
            '''
            if rtrpc.INDEX_RE_TRIGGER_ON in self.re_defs[fld]:
                try:
                    self.re_defs[fld][rtrpc.INDEX_RE_TRIGGER_ON_FUNC],   \
                    self.re_defs[fld][rtrpc.INDEX_RE_TRIGGER_ON_TEXT], = \
                        self.__create_trigger(fld, rtrpc.INDEX_RE_TRIGGER_ON)
                except TriggerDefException as e:
                    raise

            ''' Compile trigger_off...
            Take the trigger strings and compile them into static functions...
            '''
            if rtrpc.INDEX_RE_TRIGGER_OFF in self.re_defs[fld]:
                try:
                    self.re_defs[fld][rtrpc.INDEX_RE_TRIGGER_OFF_FUNC],  \
                    self.re_defs[fld][rtrpc.INDEX_RE_TRIGGER_OFF_TEXT] = \
                        self.__create_trigger(fld, rtrpc.INDEX_RE_TRIGGER_OFF)
                except TriggerDefException as e:
                    raise


        return self.get_all_fld_names()

    def get_all_fld_names(self):
        '''
        Returns a list of all field names found within all regexp patterns.
        :return:
        '''
        rtrpc = PyReParse
        # Get all field_names from all regexps
        nflds = {}
        for pat_name in self.re_defs:
            nflds = self.dict_merge(nflds, self.get_fld_names(pat_name))

        self.all_named_fields = nflds

        return self.all_named_fields

    def get_fld_names(self, repat_name):
        '''
        Returns a list of field names within a given regexp patterns.
        :return:
        '''
        rtrpc = PyReParse
        # Get all field_names from all regexps
        nflds = {}
        if repat_name in self.re_defs:
            restr = self.re_defs[repat_name][rtrpc.INDEX_RE_STRING]

            if restr:
                # Process a regexp...
                while True:
                    ng = self.re_named_group.match(restr)
                    if ng is not None:
                        fld_name = ng.group(1)
                        fld_name_expr = self.__gen_fld_name_re(fld_name)
                        nflds[fld_name] = ''
                        restr = re.sub(fld_name_expr, r'(', restr)
                    else:
                        break

        else:
            print(f"*** Error: [{repat_name}] does not exist in self.re_defs!")

        return nflds

    def __eval_triggers(self, pat_name):
        '''
        This version of __eval_triggers only expect a single re_def-name within a trigger and nothing more.
        A return value of True means that a match should be performed against the defined regexo.

        :param reg_def:
        :return:
        '''

        rtrpc = PyReParse
        trig_on_func = self.re_defs[pat_name].get(rtrpc.INDEX_RE_TRIGGER_ON_FUNC, None)
        trig_off_func = self.re_defs[pat_name].get(rtrpc.INDEX_RE_TRIGGER_OFF_FUNC, None)

        trig_on_state = True
        trig_off_state = False

        try:
            if trig_on_func is not None:
                trig_on_state = trig_on_func(self, pat_name, rtrpc.INDEX_RE_TRIGGER_ON)
        except Exception as e:
            print(f'*** Exception: \"{e}\", Hit on Evaluating Trigger_On for pattern[{pat_name}]!')

        try:
            if trig_off_func is not None:
                trig_off_state = trig_off_func(self, pat_name, rtrpc.INDEX_RE_TRIGGER_OFF)
        except Exception as e:
            print(f'*** Exception: \"{e}\", Hit on Evaluating Trigger_Off for pattern[{pat_name}]!')

        return trig_on_state and (not trig_off_state)

    def match(self, in_line, debug=False, limit_matches=None):
        in_line = in_line.rstrip()
        '''
        Given a text input line, check if any of our regexp(s) match to it.

        If we have a line specific patterns, and the current line is equal to one of them, we do try to
        match to that line-specific-match immediately. And return immediately if the regexp line
        includes the RETURN_ON_MATCH flag...

        Otherwise, we execute regexp matches against against all line-non-specific regexps in our input list.
        If any regular expressions from our input list match the line, their names are returned as a list.

        :param in_line: A string containing the line to match.
        :param debug: Emit debug lines.
        :param liit_matches: Debug - Limit the number of matches to this number.
        :return:
        '''
        rtrpc = PyReParse
        # Increment total report and page line counters
        self.report_line_count += 1
        if limit_matches:
            if limit_matches <= self.report_line_count:
                print(f'*** Exiting: limit_matches is set to [{limit_matches}]')
                sys.exit(1)
        self.section_line_count += 1
        self.subsection_line_count += 1
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
            if self.__eval_triggers(fld):
                if debug:
                    print(f'--- Triggered[{fld}]...')
                if self.re_defs[fld][rtrpc.INDEX_RE_REGEXP] is None:
                    continue
                m = self.re_defs[fld][rtrpc.INDEX_RE_REGEXP].match(in_line)
                self.re_defs[fld][rtrpc.INDEX_STATES][rtrpc.INDEX_ST_REPORT_MATCH_ATTEMPTS] += 1
                self.re_defs[fld][rtrpc.INDEX_STATES][rtrpc.INDEX_ST_SECTION_MATCH_ATTEMPTS] += 1
                if m:
                    if debug:
                        print(f'--- *** Matched[{fld}] ***')
                    # If we get a match, place values from captured groups (by name) into
                    # the self.named_field dictionary (by field name).
                    for fn in m.re.groupindex:
                        self.all_named_fields[fn] = m.group(fn)
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

                    # Perform Callback if defined...
                    if rtrpc.INDEX_RE_CALLBACK in self.re_defs[fld]:
                        # Execute the callback function.
                        self.re_defs[fld][rtrpc.INDEX_RE_CALLBACK](self, fld)

                    # Update status values of our regexps lines in the re_defs dict...
                    self.re_defs[fld][rtrpc.INDEX_STATES][rtrpc.INDEX_ST_REPORT_LINES_MATCHED] += 1
                    self.re_defs[fld][rtrpc.INDEX_STATES][rtrpc.INDEX_ST_SECTION_LINES_MATCHED] += 1
                    self.re_defs[fld][rtrpc.INDEX_STATES][
                        rtrpc.INDEX_ST_LAST_REPORT_LINE_MATCHED] = self.report_line_count
                    self.re_defs[fld][rtrpc.INDEX_STATES][
                        rtrpc.INDEX_ST_LAST_SECTION_LINE_MATCHED] = self.section_line_count
                    if matched_defs is None:
                        matched_defs = []
                    # Capture the list of re_defs entries that match this line.
                    matched_defs.append(fld)
                    # Perform FLAG based operations...
                    flags = self.re_defs[fld].get(rtrpc.INDEX_RE_FLAGS, 0)
                    if flags & rtrpc.FLAG_NEW_SECTION:
                        # Increment the section counter...
                        self.section_count += 1
                        # Reset sectional flags and counters...
                        self.section_reset()
                        # Fields that reset sections also match atleast once within those sections...
                        self.re_defs[fld][rtrpc.INDEX_STATES][rtrpc.INDEX_ST_SECTION_MATCH_ATTEMPTS] = 1
                        self.re_defs[fld][rtrpc.INDEX_STATES][rtrpc.INDEX_ST_SECTION_LINES_MATCHED] = 1
                        self.re_defs[fld][rtrpc.INDEX_STATES][rtrpc.INDEX_ST_LAST_SECTION_LINE_MATCHED] = 1
                        self.re_defs[fld][rtrpc.INDEX_STATES][rtrpc.INDEX_ST_LAST_REPORT_LINE_MATCHED] = 1
                    if flags & rtrpc.FLAG_END_OF_SECTION:
                        if self.subsection_depth > 0:
                            self.subsection_depth -= 1
                            self.current_subsection_parents.pop()
                            self.subsection_line_count = 0
                        self.section_reset()  # Existing call after
                    if flags & rtrpc.FLAG_NEW_SUBSECTION:
                        self.subsection_depth += 1
                        self.current_subsection_parents.append(fld)
                        self.subsection_depth_counts[self.subsection_depth] += 1
                        self.max_subsection_depth = max(self.max_subsection_depth, self.subsection_depth)
                        self.subsection_line_count = 1

                    # Add subsection info *after* flags for current state
                    self.last_captured_fields['subsection_depth'] = self.subsection_depth
                    self.last_captured_fields['current_subsection_parents'] = list(self.current_subsection_parents)
                    self.last_captured_fields['subsection_line_count'] = self.subsection_line_count

                    if flags & rtrpc.FLAG_RETURN_ON_MATCH:
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
                            print(f'   Report Line [{self.report_line_count}]')
                            print(f'   Section Number [{self.section_count}]')
                            print(f'   Section Line [{self.section_line_count}]')

        # TODO: Add code to check for duplicate fields found (throw error or warning)

        # Return the list of entries in the re_defs dict that match this line.
        return matched_defs, self.last_captured_fields

    def section_reset(self):
        rtrpc = PyReParse
        for fld in self.re_defs:
            self.re_defs[fld][rtrpc.INDEX_STATES][rtrpc.INDEX_ST_SECTION_MATCH_ATTEMPTS] = 0
            self.re_defs[fld][rtrpc.INDEX_STATES][rtrpc.INDEX_ST_SECTION_LINES_MATCHED] = 0
            self.re_defs[fld][rtrpc.INDEX_STATES][rtrpc.INDEX_ST_LAST_SECTION_LINE_MATCHED] = 0
        self.subsection_depth = 0
        self.current_subsection_parents = []
        self.subsection_line_count = 0

    def report_reset(self):
        rtrpc = PyReParse
        self.report_line_count = 0
        for fld in self.re_defs:
            self.re_defs[fld][rtrpc.INDEX_STATES][rtrpc.INDEX_ST_REPORT_MATCH_ATTEMPTS] = 0
            self.re_defs[fld][rtrpc.INDEX_STATES][rtrpc.INDEX_ST_REPORT_LINES_MATCHED] = 0
            self.re_defs[fld][rtrpc.INDEX_STATES][rtrpc.INDEX_ST_LAST_REPORT_LINE_MATCHED] = 0

        self.section_reset()
        self.max_subsection_depth = 0
        self.subsection_depth_counts.clear()

    def money2float(self, fld, in_str):
        re_str = re.sub(r'[\,\s\$]', r'', in_str)
        try:
            ret_val = float(re_str)
        except Exception as e:
            print(f'*** Exception: \"{e}\", Failed to convert string to float [{in_str}] -> [{re_str}]')
            print(f'    Field [{fld}] Report Line [{self.report_line_count}] ',
                  f'Section Number [{self.section_count}] ',
                  f'Section Line [{self.section_line_count}]')

        return ret_val

    def get_subsection_depth(self):
        """
        Get the current subsection depth (nesting level).
        :return: int - 0 for top-level, >0 for subsections.
        """
        return getattr(self, 'subsection_depth', 0)

    def get_current_subsection(self):
        """
        Get the current subsection parents as a tuple.
        :return: tuple - e.g., ('report_id', 'customer_id')
        """
        return tuple(getattr(self, 'current_subsection_parents', []))

    def get_max_subsection_depth(self):
        """
        Get the maximum subsection depth observed.
        :return: int
        """
        return getattr(self, 'max_subsection_depth', 0)

    def get_subsection_depth_counts(self):
        """
        Get counts of subsections per depth.
        :return: dict - e.g., {1: 10, 2: 5}
        """
        return dict(getattr(self, 'subsection_depth_counts', {}))

    def get_subsection_info(self):
        """
        Get comprehensive subsection information.
        :return: dict with depth, parents, max_depth, counts.
        """
        return {
            'depth': self.get_subsection_depth(),
            'parents': list(self.get_current_subsection()),
            'max_depth': self.get_max_subsection_depth(),
            'counts': self.get_subsection_depth_counts()
        }

    def money2decimal(self, fld, in_str):
        re_str = re.sub(r'[\,\s\$]', r'', in_str)
        try:
            ret_val = Decimal(re_str)
        except Exception as e:
            ret_val = Decimal('0')
        return ret_val

    def _find_section_boundaries(self, file_path: str) -> List[Tuple[int, int]]:
        """
        Find boundaries of top-level sections in the file for parallel processing.
        This identifies start and end lines of sections based on boundary patterns.
        Handles basic nesting but returns top-level boundaries for parallel_depth=1.

        :param file_path: Path to the file to analyze.
        :return: List of tuples (start_line, end_line) where lines are 1-based.
        """
        start_lines = []
        with open(file_path, 'r') as f:
            for i, line in enumerate(f, 1):
                line_stripped = line.rstrip('\n')
                matched = False
                for name, defn in self.re_defs.items():
                    flags = defn.get(self.INDEX_RE_FLAGS, 0)
                    if flags & self.FLAG_NEW_SECTION:
                        regexp = defn.get(self.INDEX_RE_REGEXP)
                        if regexp and regexp.match(line_stripped):
                            start_lines.append(i)
                            matched = True
                            break
                if matched:
                    continue

        # Get total lines
        total_lines = 0
        with open(file_path, 'r') as f:
            total_lines = sum(1 for _ in f)

        boundaries = []
        for j in range(len(start_lines)):
            start = start_lines[j]
            end = start_lines[j + 1] - 1 if j + 1 < len(start_lines) else total_lines
            boundaries.append((start, end))

        return boundaries

    def _process_section_chunk(self, file_path: str, start_line: int, end_line: int) -> Dict[str, Any]:
        """
        Process a specific chunk of lines corresponding to a section.
        Creates a new PyReParse instance to avoid state conflicts in parallel execution.

        :param file_path: Path to the file.
        :param start_line: Starting line number (1-based, inclusive).
        :param end_line: Ending line number (1-based, inclusive).
        :return: Dictionary containing section data, including matched fields.
        """
        prp = PyReParse(self.raw_patterns)
        prp.set_file_name(file_path)
        prp.report_reset()
        prp.section_reset()

        with open(file_path, 'r') as f:
            all_lines = f.readlines()
            lines = all_lines[start_line - 1 : end_line]

        section_data = {
            'section_start': start_line,
            'fields_list': [],
            'totals': {},
            'valid': True
        }
        for line in lines:
            match_def, fields = prp.match(line.rstrip())
            if match_def:
                section_data['fields_list'].append({
                    'match_def': match_def,
                    'fields': fields.copy()
                })
        return section_data

    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Serial parsing returning same format as parse_file_parallel(depth=0).
        """
        boundaries = self._find_section_boundaries(file_path)
        sections = []
        for start, end in boundaries:
            sec = self._process_section_chunk(file_path, start, end)
            sections.append(sec)
        return sections

    def parse_file_parallel(self, file_path: str, max_workers: int = 4, parallel_depth: int = 1) -> List[Dict[str, Any]]:
        """
        Parse the entire file in parallel by dividing it into section chunks and processing them concurrently.
        Currently supports top-level sections (parallel_depth=1). Higher depths are stubbed for future recursion.

        :param file_path: Path to the file to parse.
        :param max_workers: Maximum number of worker threads to use.
        :param parallel_depth: Depth of parallelism (1 for top-level sections only).
        :return: List of dictionaries, each representing parsed data for a section.
        """
        if parallel_depth > 1:
            raise NotImplementedError("TODO: Recurse into subsections for parallel_depth > 1")

        if not hasattr(self, 'raw_patterns'):
            raise ValueError("Patterns must be loaded first using load_re_lines()")

        boundaries = self._find_section_boundaries(file_path)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(self._process_section_chunk, file_path, s, e)
                for s, e in boundaries
            ]
            sections = [future.result() for future in futures]

        sections.sort(key=lambda x: x['section_start'])
        return sections
