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
- Additional benefits include the ability to crosscheck a non-matching line witch
a simpler regexp that can catch lines that should have matched but did not
due to a need to tweak the main regexp, or possible a corrupt input line.
- Logic for counting report lines and sections within a report.
- Uses named-capture-groups and returns captured values in a dictionary.
<br>

## Basic Usage Pattern

1. Set up the named-regexp(s) with named-capture-groups data structure, along with associated properties:
   1. Flags:
      1. Only once
      2. Start of Section
   2. Trigger ON/OFF
      1. trigger matching on or off based on another named regexp
   3. Optional Quick-Check RegExp)
      1. If the current named-regexp fails to match the given line. The quick-check regexp is run, and if a match occurs, warns that a regexp may have missed a line. So either the named-regexp is wrong, or the quick-check is produced a false positive.
   4. TODO: callback
      1. On match, run the stated callback function to perform validations and processing logic. In fact, all processig logic can be implemented within callbacks.
   5. Write processing logic...
      1. If all processing logic is implemented as callbacks, the main logic would look like... <i>(TODO: Callbacks implemented soon...)</i>
         1. ``` 
            with open(file_path, 'r') as txt_file:
               for line in txt_file:
                   match_def, matched_fields = rtp.match(line)
            ```
      2. With or without Callback, you can trigger logic when name-regexp fields match using (see [tests](src/pyreparse/tests/test_pyreparse.py) as an example)...
         1. ```
            with open(file_path, 'r') as txt_file:
               for line in txt_file:
                   match_def, matched_fields = rtp.match(line)
                   if match_def[0] = 'regexp_A':
                        ...         
                   elif match_def[0] = 'regexp_B':
                        ...         
            ```      
<br>

## License...

Apache 2.0
