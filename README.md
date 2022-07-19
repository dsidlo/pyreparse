# PyReParse
PyReParse is a library the helps to ease the development processes of parsing
complex reports, which have enough structure for effective regular expression 
processing.
<br>

## Benefits...

- The benefits of using PyReParse include...
- The use of a standard data structure for holding regular expressions. 
Associated to the regexp are additional flags and fields that help to reduce the
number of times a given regexp is executed.
- Regexp processing can be expensive. The goal is to run regexp matches only when they 
are needed. So if you know that the pattern for regexp A always occurs before
regexp B, use can use the data structure to specify that regexp B should not
be used until after regexp A triggers.
- All regular expressions and their associated properties are in one data structure.
- Additional benefits include the ability to crosscheck a non-matching line which
a simpler regexp that can catch lines that should have matched but did not
due to a need to tweak the main regexp, or possible a corrupt input line.
- Logic for counting report lines and sections within a report.
- Uses named-capture-groups and returns captured values in a dictionary.
<br>

## Basic Usage Pattern

1. Set up the named-regexp-pattern(s) with named-capture-groups data structure, along with associated properties (see [example](src/pyreparse/tests/test_pyreparse.py?plain=1#L46) in test code...):
   1. Flags:
      1. Only once
      2. Start of Section
   2. Trigger ON/OFF
      1. trigger matching on or off based on another named regexp
   3. Optional Quick-Check RegExp)
      1. If the current named-regexp fails to match the given line. The quick-check regexp is run, and if a match occurs, warns that a regexp may have missed a line. So either the named-regexp is wrong, or the quick-check is produced a false positive.
   4. callback(<PyReParse_Instance>, <regexp_pattern_name>)
      1. On match, run the stated callback function to perform validations and processing logic. In fact, all processing logic can be implemented within callbacks.
      2. The Callback function is called when a match occurs and after fields have been captured.
      3. Callbacks can be used for field validation and event correlation, as the PyReParase instance (which contains the states of all regexp/fields), is available to the callback.
   5. Write the document processing logic...
      1. If all processing logic is implemented as callbacks, the main logic would look like... <i>(TODO: Callbacks implemented soon...)</i>
         1. ``` 
            # Import PyRePrase
            from pyreparse import PyReParse as PRP
            
            # Define callback functions...
            def on_pattern001(prp_instance, pat_name):
               if fld_name != 'pattern001':
                  print(f'Got wrong pattern name [{pat_name}].')
            
            # Define our Regular Expression Patterns Data Structure...
            regexp_pats = {
               'pattern_001': {
                  InDEX_RE: '^Test\s+Pattern\s+(?P<pat_val>\d+)'
                  <INDEX_RE...>: 'value',
                  <INDEX_RE...>: 'value',
                  INDEX_RE_CALLBACK: on_pattern_001
                     ...
               },
               ...
            }
            
            # Create and Instance of PyRePrase
            prp = PRP(<regexp_pats>)
            
            # Open the input file...
            with open(file_path, 'r') as txt_file:
            
               # Process each line of the input file...
               for line in txt_file:
            
                  # This call on prp.match(<input_line>) to process the line
                  # against our data structure of regexp patterns.
                  match_def, matched_fields = prp.match(line)
            ```
      2. With or without Callback, you can trigger logic when name-regexp fields match using (see [tests](src/pyreparse/tests/test_pyreparse.py?plain=57#L254) as an example)...
         1. ```
            ...
            
            # Open the input file...
            with open(file_path, 'r') as txt_file:
            
               # Process each line of the input file...
               for line in txt_file:
            
                  # This call on prp.match(<input_line>) to process the line
                  # against our data structure of regexp patterns.
                  pattern_name, matched_fields = prp.match(line)
            
                  # Then, we have logic based on which pattern matched,
                  # and/or values in captured fields...
                   if match_def[0] = 'pattern_001':
                        ...         
                   elif match_def[0] = 'pattern_002':
                        ...         
            ```      
<br>

## License...

Apache 2.0
