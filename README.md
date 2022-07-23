# PyReParse
PyReParse is a library the helps to ease the development processes of parsing
complex reports, which have enough structure for effective regular expression 
processing.

PyReParse is a library that helps one create parsing engines for formed text reports. I had a such a need when I was tasked to parse a Financial Institution's archived transaction reports where the databases that held this data no-longer existed. So the data in the report forms was the only data available to re-create the original database. Thus, regular-expressions were used to find and capture certain field values, and validation calculations were needed to ensure that the data going into the database was complete and accurate.

<br>

## Benefits...

- The benefits of using PyReParse include...
- The use of a standard data structure for holding regular expressions. 
Associated to the regexp are additional flags and fields that help to reduce the
number of times a given regexp is executed.
- Regexp processing can be expensive. The goal is to run regexp matches only when they 
are needed. So if you know that the pattern for regexp A always occurs before
regexp B, you can use the data structure to specify that regexp B should not
be used until after regexp A triggers.
- All regular expressions and their associated properties are in one data structure.
- Additional benefits include the ability to crosscheck a non-matching line which
a simpler regexp that can catch lines that should have matched but did not,
due to a need to tweak the main regexp, or possibly a corrupt input line.
- Logic for counting report lines and sections within a report.
- PyReParse uses named-capture-groups and returns captured values in a dictionary. This eases the ability to capture values for transformation and storage.
- One can associate a RegExp pattern to a callback so that one can perform custom calculations, validations, and transforations to the captured values of interest.
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
         1. ```python
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
         1. ```python
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

Please check out [pyreparse_example.py](pyreparse/example/pyreparse_example.py), you can used this code as a template to guide you in the creation of your own parsing engine.

## The PyReParse Data Structure of Patterns
<br>

## Flags

## Coding Triggers...
A trigger is a line of logic that references counters or pattern-names. Triggers can use the full depth of python expressions, and are compiled to a call back function for efficiency. The purpose of the trigger is to simply return true or false. For the **trigger-on**, the expression should return true if the RegExp Pattern is to be evaluated against the current and following lines. For **trigger-off**, it should evaluate to True so that it is not evaluated for the current and subsequent lines. 

### < Counters >
Counters are synbolic names that are enclosed in Less-Than and Greater-Than signs. 

The following is te current list of supported report counters...

 - **<REPORT_LINE>**
   - The **<REPORT_LINE>** counter increments by 1 for each line that the _match()_ method is called on.
 - **<SECTION_NUMBER>**
   - The **<SECTION_NUMBER>** counter increments by 1 for each time a _match()_ occurs on a pattern that has the flag **PyReParse.FLAG_NEW_SECTION**.
 - **<SECTION_LINE>**
   - The **<SECTION_LINE>** counter increments by 1 for each line that the _match()_ method is called on that is part of a section.

All counters start at 0.

### {Pattern_Names}
Pattern names are symbolic references to the RegExp Patterns in the current PyReParse data structure.
Each Pattern may be associated to triggers that tell the matcher when or when not to execute a match on a given pattern. Triggers improve the efficiency of RegExp processing by reducing the number of Regular Expressions that are executed on any given line. This can be very effective when processing a huge number of documents. The pattern name evaluates to True if the pattern has been matched, and False if the pattern as not been matched since the last "NEW_SECTION", A "New Section" occurs when a pattern that has the flag **PyReParse.FLAG_NEW_SECTION** matches the current line, and it triggers the reset of section counters.

## Coding Callbacks...
You may also code callbacks that are executed when a pattern matches. The callback function is called when a pattern matches, and after the fields have been captured. The callback function is passed the PyReParse instance, and the name of the pattern that matched. The callback function can then use the PyReParse instance to access any currently captured fields, and perform any processing logic field value updates.

<br>
## License...

Apache 2.0
