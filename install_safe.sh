#!/bin/bash

echo "======================================"
echo " SAFE PYTHON INSTALLER FOR BAD NETWORK "
echo "======================================"

REQ_FILE="requirements.txt"
DEPS_DIR="deps"

# Check if requirements.txt exists
if [ ! -f "$REQ_FILE" ]; then
    echo "ERROR: $REQ_FILE not found!"
    exit 1
fi

# Create deps folder if missing
if [ ! -d "$DEPS_DIR" ]; then
    echo "Creating deps directory..."
    mkdir $DEPS_DIR
fi

echo ""
echo "STEP 1: Downloading Python packages safely..."
echo "This may take time. If the network breaks, run the script again."
echo ""

pip download \
    --default-timeout=200 \
    --retries=20 \
    --no-cache-dir \
    -r $REQ_FILE \
    -d $DEPS_DIR

if [ $? -ne 0 ]; then
    echo "WARNING: Some downloads may have failed."
    echo "Run this script again to continue downloading."
else
    echo "All packages downloaded successfully."
fi

echo ""
echo "STEP 2: Installing packages offline..."
echo ""

pip install \
    --no-index \
    --find-links=$DEPS_DIR \
    --upgrade \
    --upgrade-strategy eager \
    -r $REQ_FILE

echo ""
echo "======================================"
echo "       INSTALLATION COMPLETED!"
echo "======================================"
