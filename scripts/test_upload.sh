#!/bin/bash

BASE_URL="http://localhost:5328"

echo "Testing Upload API at $BASE_URL/api/upload"

echo "------------------------------------------------"
echo "1. Uploading Binary CSV (multipart/form-data)..."
curl -X POST -F "file=@./dev-samples/sales_demo.csv" "$BASE_URL/api/upload"
echo -e "\n"

echo "------------------------------------------------"
echo "2. Uploading via JSON URL..."
curl -X POST -H "Content-Type: application/json" \
     -d '{"fileUrl":"https://example.com/sales_demo.csv","filename":"sales_demo.csv"}' \
     "$BASE_URL/api/upload"
echo -e "\n"

echo "------------------------------------------------"
echo "3. Expecting Error (Invalid Extension .txt)..."
# Create dummy txt
echo "dummy" > dummy.txt
curl -X POST -F "file=@dummy.txt" "$BASE_URL/api/upload"
rm dummy.txt
echo -e "\n"

echo "------------------------------------------------"
echo "Done."
