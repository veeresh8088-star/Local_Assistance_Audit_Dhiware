import json
data = json.load(open('use_cases_full.json', encoding='utf-8'))
for d in data:
    print(f"UC{d['sl']}: {d['use_case'][:120]}")
    print(f"   FILE FORMAT: {d['file_format']}")
    print(f"   INPUT FILE:  {d['input_file']}")
    print(f"   EXPECTED:    {d['expected_result'][:120]}")
    print()
