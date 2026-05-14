import pandas as pd
import json

df = pd.read_excel('AICyberAuditBox Use Cases List.xlsx', header=1)
df.columns = ['sl', 'use_case', 'pre_req', 'expected_result', 'status', 'input_file', 'file_format', 'remarks']
df = df.dropna(subset=['use_case'])

result = []
for _, row in df.iterrows():
    result.append({
        "sl": str(row['sl']),
        "use_case": str(row['use_case']),
        "expected_result": str(row['expected_result']),
        "file_format": str(row['file_format']),
        "input_file": str(row['input_file'])
    })

with open('use_cases_full.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print("Done - wrote use_cases_full.json")
