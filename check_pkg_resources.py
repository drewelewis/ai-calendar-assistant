import subprocess
import sys

def check_pkg_resources():
    """Check for pkg_resources related issues"""
    
    print("=== Checking pkg_resources issues ===")
    
    # Check if pkg_resources is available
    try:
        import pkg_resources
        print(f"✅ pkg_resources available: {pkg_resources.__file__}")
        print(f"   Version: {pkg_resources.__version__}")
    except ImportError as e:
        print(f"❌ pkg_resources not available: {e}")
    except Exception as e:
        print(f"⚠️  pkg_resources error: {e}")
    
    # Check setuptools
    try:
        import setuptools
        print(f"✅ setuptools available: {setuptools.__version__}")
    except ImportError as e:
        print(f"❌ setuptools not available: {e}")
    
    # Check if we can import from pkg_resources
    try:
        from pkg_resources import iter_entry_points
        print("✅ iter_entry_points import successful")
    except ImportError as e:
        print(f"❌ iter_entry_points import failed: {e}")
    except Exception as e:
        print(f"⚠️  iter_entry_points error: {e}")
    
    # Check Python version
    print(f"\n🐍 Python version: {sys.version}")
    
    # Check for packages that might use pkg_resources
    packages_to_check = [
        'opentelemetry',
        'azure-monitor-opentelemetry', 
        'semantic-kernel',
        'fastapi',
        'uvicorn'
    ]
    
    print(f"\n📦 Checking for packages that might use pkg_resources:")
    result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        installed = result.stdout.lower()
        for pkg in packages_to_check:
            if pkg in installed:
                print(f"   ✅ {pkg} - installed")
            else:
                print(f"   ❌ {pkg} - not found")

if __name__ == "__main__":
    check_pkg_resources()
