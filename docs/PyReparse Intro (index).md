# PyReparse

## Python Report Parser

 - Create custom engines for efficiently parsing tabular reports and structured 
   or semi-structured documents.
 - Processing documents using regular expression is normaly slow because loops 
   of regular expressions might be run against a given line on the report needlessly
   to determine the type of line one is looking at.
 - What sets PyReparse apart, is that regular expressions are performed only
   when they are needed, and only when it is very likely that the data in the
   report will more than likely mmatch the regular expression.
   This allows PyReparse to tackle massive report datasets very quickly.

## When to use PyReparse

  - You have a massive set of archived reports, and you need to do some data 
    analytics on it.
  - You don't have the resources to process the data using big data tools.
  - It would be faster to just process the data as it is rather than parse
    and load it into a database, then performing queries.
  - You only want to load data into a database for specific customers or data
    found in the massive set of reports.

## Defining the Parsing Data Structure

  - Defining the Parsing Data Structure and accompanying program that processes
    the data captured can be challenging to navigate, But this is where today's
    LLMs can be very helpful in getting started.

