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
