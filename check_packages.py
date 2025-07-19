#!/usr/bin/env python3
try:
    import azure.identity
    print('✅ azure.identity: Available')
except ImportError:
    print('❌ azure.identity: Missing')

try:
    import aiohttp
    print('✅ aiohttp: Available')
except ImportError:
    print('❌ aiohttp: Missing')

try:
    import azure.core
    print('✅ azure.core: Available')
except ImportError:
    print('❌ azure.core: Missing')
