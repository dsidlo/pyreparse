# PyReParse Changes v0.0.4

## Changes in v0.0.4
  - Added Money Handling
    - Money can should be handled using Decimal rather than Float to remove the possibility of rounding errors.
    - To use the money type for a field that is captured during parsing...
      - Use the m_flds[] dictionary when defining the field name and what it captures: `m_flds['nsf_fee'] = ...`
  
