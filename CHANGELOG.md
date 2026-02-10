# PyReParse Change Log

## Changes in v0.0.4
  - Added Money Handling
    - Money can should be handled using Decimal rather than Float to remove the possibility of rounding errors.
    - To use the money type for a field that is captured during parsing...
      - Use the m_flds[] dictionary when defining the field name and what it captures: `m_flds['nsf_fee'] = ...`
  
  - Added Section and nested Subsection detection and counting.
  - Added validate_re_defs() function that validate the data structure of patterns that PyReParse uses to parse the structure text.
  - Added parallel execution by section
    - parse_file()
    - parse_file_parallel(file_path: str, max_workers: int = 4, parallel_depth: int = 1) -> List[Dict[str, Any]]
  - Added regexp caching so that regexps are compiled only once.
  - Implement a streaming API mode for low memory systems
    - This overcomes the potential memory limitation that parse_file() and parse_file_parallel() have as those functions collect data into a memory structure. But if the files are extreemly large and have a lot of data, the memory structure of the captured data can also become quote large. So, where as the stream_matches() does not accumulate a memory structure of the data and instead, operates on the data as it streams in, much like the PyReParse.match() function already does. But if one uses stream_matches() on execute all logic in callbacks.
