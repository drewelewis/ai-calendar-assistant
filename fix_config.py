import re

# Read the file with UTF-8 encoding
with open('telemetry/config.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace console function calls with print statements
content = re.sub(r'console_info\((.*?)\)', r'print(\1)', content)
content = re.sub(r'console_warning\((.*?)\)', r'print(\1)', content)  
content = re.sub(r'console_error\((.*?)\)', r'print(\1)', content)
content = re.sub(r'console_debug\((.*?)\)', r'print(\1)', content)

# Write back the file with UTF-8 encoding
with open('telemetry/config.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed all console function calls in config.py')
