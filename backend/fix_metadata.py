#!/usr/bin/env python3
"""
Fix metadata references in API files
"""

import os
import re
from pathlib import Path

def fix_metadata_in_file(file_path):
    """Replace metadata= with meta_data= in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace metadata= with meta_data=
        updated_content = content.replace('metadata={', 'meta_data={')
        
        if content != updated_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print(f"✅ Fixed {file_path}")
            return True
        else:
            print(f"⏭️  No changes needed in {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

def main():
    """Fix all API files"""
    api_dir = Path("app/api")
    
    if not api_dir.exists():
        print("❌ API directory not found")
        return
    
    files_fixed = 0
    for py_file in api_dir.glob("*.py"):
        if fix_metadata_in_file(py_file):
            files_fixed += 1
    
    print(f"\n🎉 Fixed {files_fixed} files")

if __name__ == "__main__":
    main()
