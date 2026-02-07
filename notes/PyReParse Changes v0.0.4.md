# PyReParse Changes v0.0.4

## Changes in v0.0.4
  - Added Money Handling
    - Money can should be handled using Decimal rather than Float to remove the possibility of rounding errors.
    - To use the money type for a field that is captured during parsing...
      - Use the m_flds[] dictionary when defining the field name and what it captures: `m_flds['nsf_fee'] = ...`
  
  - Added Section and nested Subsection detection and counting.

## An example of Section and Subsection usage

### Section/Subsection Detection in PyReParse Data Structure

**Detection Mechanism:**
- **Data Structure (patterns dict):** Each pattern entry specifies:
  - `INDEX_RE_STRING`: RegEx with named groups.
  - `INDEX_RE_FLAGS`: Bitflags like `FLAG_NEW_SECTION` (2: starts section, inc `section_count`, reset section states), `FLAG_NEW_SUBSECTION` (32: nests under current, inc `subsection_depth`, append parent pat to `current_subsection_parents`, update counts/max/line).
  - `INDEX_RE_TRIGGER_ON/OFF`: Strings compiled to funcs (e.g., `'{report_id}'` = matched since last reset; `<SECTION_LINE> >= 2`).
- **Runtime (`match(line)`):**
  - Inc counters: `report_line_count`, `section_line_count`, `subsection_line_count`.
  - Eval triggers → if on & not off, run RegEx.
  - On match + flag:
    - NEW_SECTION: `section_count +=1`, `section_reset()` (resets sub too).
    - NEW_SUBSECTION: `depth +=1`, `parents.append(pat_name)`, `line_count=1`.
    - END_OF_SECTION: Pop innermost sub (if depth>0), `section_reset()`.
  - Add sub info to `last_captured_fields` post-flags.
  - Expose: `get_subsection_depth()`, `get_current_subsection()` (tuple parents), `get_subsection_info()` dict.
- **Resets:** `section_reset()`/ `report_reset()` clear sub states.

**Usage in Parsing Code:**
Stream lines, react to matches/flags via `match_def`/`fields`. Subs enable hierarchy (report > customer > tx).

**Input Date Example***
```text
**BP0420170101REPOREPORT-PAID-NSF
CUSTOMER: 12345
   394654-54  $  5.41
   394654-54  $  5.41
TOTAL: $10.82

**BP0420170102NEXT-REPORT
CUSTOMER: 67890
   111111-11  $  3.00
TOTAL: $3.00
```
**Coding Example** (Hierarchical NSF Report Parser):
```python
from pyreparse import PyReParse as PRP
from collections import defaultdict

# Patterns Data Structure
patterns = {
    'report_id': {
        PRP.INDEX_RE_STRING: r'^\*\*(?P<report_id>[^\s]+)\s*$',
        PRP.INDEX_RE_FLAGS: PRP.FLAG_NEW_SECTION | PRP.FLAG_RETURN_ON_MATCH,
        PRP.INDEX_RE_TRIGGER_ON: '<REPORT_LINE> == 1',
        PRP.INDEX_RE_TRIGGER_OFF: '{report_id}',
    },
    'customer_id': {
        PRP.INDEX_RE_STRING: r'^CUSTOMER:\s+(?P<cust_id>\d+)',
        PRP.INDEX_RE_FLAGS: PRP.FLAG_NEW_SUBSECTION | PRP.FLAG_RETURN_ON_MATCH,
        PRP.INDEX_RE_TRIGGER_ON: '{report_id}',  # After report start
        PRP.INDEX_RE_TRIGGER_OFF: '{cust_total}',
    },
    'tx_line': {
        PRP.INDEX_RE_STRING: r'^\s+(?P<ac_num>\d+)-(?P<ac_type>\d+)\s+(?P<amt>\$[\d,]+\.\d\d)',
        PRP.INDEX_RE_TRIGGER_ON: '{customer_id}',
        PRP.INDEX_RE_TRIGGER_OFF: '{cust_total}',
    },
    'cust_total': {
        PRP.INDEX_RE_STRING: r'^TOTAL:\s+(?P<total>\$[\d,]+\.\d\d)',
        PRP.INDEX_RE_FLAGS: PRP.FLAG_END_OF_SECTION,
        PRP.INDEX_RE_TRIGGER_ON: '<SUBSECTION_DEPTH> == 1',  # Depth 1 (customer)
        PRP.INDEX_RE_TRIGGER_OFF: '{cust_total}',
    },
}

prp = PRP(patterns)
prp.set_file_name('data/SectionTestData/section_test.txt')

reports = []  # List of {'report_id': str, 'customers': list}
current_report = None
current_cust = None

with open('data/SectionTestData/section_test.txt') as f:
    for line in f:
        match_def, fields = prp.match(line.strip())
        info = prp.get_subsection_info()
        print(f"Depth {info['depth']}, Parents {info['parents']}: {match_def} {fields}")

        if match_def and 'report_id' in match_def:
            current_report = {'id': fields['report_id'], 'customers': []}
            reports.append(current_report)
        elif match_def and 'customer_id' in match_def:
            current_cust = {'id': fields['cust_id'], 'txs': [], 'total': 0}
            current_report['customers'].append(current_cust)
            print(f"New customer under {info['parents']}")
        elif match_def and 'tx_line' in match_def:
            current_cust['txs'].append(fields['amt'])
        elif match_def and 'cust_total' in match_def:
            current_cust['total'] = fields['total']
            # Validate sum(tx) == total

print(f"Parsed {len(reports)} reports, max sub-depth {prp.get_max_subsection_depth()}")
```

**Output Sample:**
```
❯ python section_subsection_test.py 
Depth 0, Parents []: ['report_id'] {'report_id': 'BP0420170101REPOREPORT-PAID-NSF', 'subsection_depth': 0, 'current_subsection_parents': [], 'subsection_line_count': 0}
Depth 1, Parents ['customer_id']: ['customer_id'] {'cust_id': '12345', 'subsection_depth': 1, 'current_subsection_parents': ['customer_id'], 'subsection_line_count': 1}
New customer under ['customer_id']
Depth 1, Parents ['customer_id']: None {}
Depth 1, Parents ['customer_id']: None {}
Depth 0, Parents []: ['cust_total'] {'total': '$10.82', 'subsection_depth': 0, 'current_subsection_parents': [], 'subsection_line_count': 0}
Depth 0, Parents []: None {}
Depth 0, Parents []: ['report_id'] {'report_id': 'BP0420170102NEXT-REPORT', 'subsection_depth': 0, 'current_subsection_parents': [], 'subsection_line_count': 0}
Depth 1, Parents ['customer_id']: ['customer_id'] {'cust_id': '67890', 'subsection_depth': 1, 'current_subsection_parents': ['customer_id'], 'subsection_line_count': 1}
New customer under ['customer_id']
Depth 1, Parents ['customer_id']: None {}
Depth 0, Parents []: ['cust_total'] {'total': '$3.00', 'subsection_depth': 0, 'current_subsection_parents': [], 'subsection_line_count': 0}
Parsed 2 reports, max sub-depth 1
```

Triggers/flags minimize RegEx runs; subs track hierarchy for nested accumulations/validations. See `tests/test_pyreparse.py` for more.