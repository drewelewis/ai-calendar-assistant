import re
import os

files_to_fix = [
    'telemetry/token_tracking.py',
    'telemetry/decorators.py'
]

for file_path in files_to_fix:
    if os.path.exists(file_path):
        print(f"Fixing {file_path}...")
        
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove the console_output import
        content = re.sub(r'from \.console_output import.*?\n', '', content)
        
        # Replace console function calls with print or remove them
        content = re.sub(r'console_token_usage\([^)]+\)', '# Token usage logged', content)
        content = re.sub(r'console_telemetry_event\([^)]+\)', '# Telemetry event logged', content)
        content = re.sub(r'console_span_start\([^)]+\)', '# Span start logged', content)
        content = re.sub(r'console_span_end\([^)]+\)', '# Span end logged', content)
        content = re.sub(r'console_debug\([^)]+\)', '# Debug logged', content)
        
        # Write back the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Fixed {file_path}")
    else:
        print(f"File {file_path} not found")

print('All telemetry files fixed!')
