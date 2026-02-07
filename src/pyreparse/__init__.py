"""

PyReParse is a library that helps one create parsing engines for formed text reports.
I had a such a need when I was tasked to parse a Financial Institution's archived transaction reports
where the databases that held this data no-longer existed. So the data in the report forms was the only
data available to re-create the original database. Thus, regular-expressions were used to find and capture
certain field values, and validation calculations were needed to ensure that the data going into the
database was complete and accurate.

Benefits...

- The benefits of using PyReParse include...
- The use of a standard data structure for holding regular expressions.
Associated to the regexp are additional flags and fields that help to reduce the
number of times a given regexp is executed.
- Regexp processing can be expensive. The goal is to run regexp matches only when they
are needed. So if you know that the pattern for regexp A always occurs before
regexp B, you can use the data structure to specify that regexp B should not
be used until after regexp A triggers.
- All regular expressions and their associated properties are in one data structure.
- Additional benefits include the ability to cross-check a non-matching line with
a simpler regexp that can catch lines that should have matched but did not,
due to a need to tweak the main regexp, or possibly a corrupt input line.
- Logic for counting report lines and sections within a report.
- PyReParse uses named-capture-groups and returns captured values in a dictionary.
  This eases the ability to capture values for transformation and storage.
- One can associate a RegExp pattern to a callback so that one can perform custom calculations, validations,
  and transformations to the captured values of interest.

"""
from .PyReParse import PyReParse
