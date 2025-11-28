#!/usr/bin/env python3
"""Check registered routes in FastAPI app"""

import main

print("Registered Routes:")
for route in main.app.routes:
    if hasattr(route, 'methods'):
        print(f"  - {route.path} {list(route.methods)}")
    else:
        print(f"  - {route.path} [WebSocket]")

print("\nChecking for /api/feedback endpoint...")
feedback_routes = [r for r in main.app.routes if '/api/feedback' in r.path]
if feedback_routes:
    print("SUCCESS: /api/feedback endpoint is registered!")
    for r in feedback_routes:
        print(f"  Methods: {list(r.methods)}")
else:
    print("ERROR: /api/feedback endpoint NOT found!")
