#!/usr/bin/env python3
"""
Fix all console imports to use direct imports from telemetry.console_output
"""

import os
import re

def fix_console_imports():
    """Update files to use direct console imports"""
    
    files_to_fix = [
        "ai/agent.py",
        "plugins/graph_plugin.py", 
        "test_multi_agent.py"
    ]
    
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            print(f"Fixing {file_path}...")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Make sure the file has the direct import
            if "from telemetry.console_output import" not in content:
                # Add the import after the last import
                lines = content.split('\n')
                last_import_idx = -1
                
                for i, line in enumerate(lines):
                    if line.strip().startswith('import ') or line.strip().startswith('from '):
                        last_import_idx = i
                
                if last_import_idx >= 0:
                    lines.insert(last_import_idx + 1, "from telemetry.console_output import console_info, console_debug, console_warning, console_error, console_success, console_telemetry_event")
                    content = '\n'.join(lines)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Fixed {file_path}")
        else:
            print(f"⚠️ File not found: {file_path}")

if __name__ == "__main__":
    fix_console_imports()
    print("All console imports fixed!")
