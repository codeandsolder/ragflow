#!/bin/bash

# Test script for Docker API Proxy

echo "Testing Docker API Proxy..."
echo "======================="

# Check if proxy is running
if ! curl -f http://localhost:2376/_ping > /dev/null 2>&1; then
    echo "❌ Docker API Proxy is not running on port 2376"
    exit 1
fi

echo "✅ Docker API Proxy is running"

# Test allowed operations
echo ""
echo "Testing allowed operations..."
echo "----------------------------"

# Test container creation (should succeed)
echo -n "Testing container creation: "
if curl -X POST http://localhost:2376/containers/create \
    -H "Content-Type: application/json" \
    -d '{"Image": "alpine", "Cmd": ["echo", "test"]}' > /dev/null 2>&1; then
    echo "✅ Allowed"
else
    echo "❌ Failed"
fi

# Test images listing (should succeed)
echo -n "Testing images listing: "
if curl -X GET http://localhost:2376/images/json > /dev/null 2>&1; then
    echo "✅ Allowed"
else
    echo "❌ Failed"
fi

# Test system info (should succeed)
echo -n "Testing system info: "
if curl -X GET http://localhost:2376/info > /dev/null 2>&1; then
    echo "✅ Allowed"
else
    echo "❌ Failed"
fi

# Test blocked operations
echo ""
echo "Testing blocked operations..."
echo "----------------------------"

# Test volume creation (should be blocked)
echo -n "Testing volume creation: "
if curl -X POST http://localhost:2376/volumes/create \
    -H "Content-Type: application/json" \
    -d '{"Name": "test"}' > /dev/null 2>&1; then
    echo "❌ Failed (should be blocked)"
else
    echo "✅ Blocked (expected)"
fi

# Test network creation (should be blocked)
echo -n "Testing network creation: "
if curl -X POST http://localhost:2376/networks/create \
    -H "Content-Type: application/json" \
    -d '{"Name": "test"}' > /dev/null 2>&1; then
    echo "❌ Failed (should be blocked)"
else
    echo "✅ Blocked (expected)"
fi

# Test privileged operations (should be blocked)
echo -n "Testing privileged container creation: "
if curl -X POST http://localhost:2376/containers/create \
    -H "Content-Type: application/json" \
    -d '{"Image": "alpine", "HostConfig": {"Privileged": true}}' > /dev/null 2>&1; then
    echo "❌ Failed (should be blocked)"
else
    echo "✅ Blocked (expected)"
fi

echo ""
echo "====================="
echo "✅ All tests completed"
