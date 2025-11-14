#!/bin/bash
set -e

echo "========================================="
echo "InstructLab Setup Script"
echo "========================================="

# Check if running in RHOAI workbench
if [ -d "/opt/app-root" ]; then
    echo "✓ Running in RHOAI workbench"
else
    echo "⚠ Not in RHOAI environment"
fi

# Install InstructLab
echo ""
echo "📦 Installing InstructLab..."
pip install --upgrade pip
pip install instructlab

# Initialize InstructLab
echo ""
echo "⚙️  Initializing InstructLab..."
ilab config init --non-interactive

# Create taxonomy structure
echo ""
echo "📁 Creating taxonomy directories..."
mkdir -p taxonomy/security
mkdir -p taxonomy/recruiter
mkdir -p datasets/generated
mkdir -p models

# Verify taxonomy files
echo ""
echo "🔍 Checking taxonomy files..."
if [ -f "taxonomy/security/qna.yaml" ]; then
    echo "✓ taxonomy/security/qna.yaml found"
else
    echo "✗ taxonomy/security/qna.yaml NOT FOUND"
    echo "  Create this file before generating data"
fi

if [ -f "taxonomy/recruiter/qna.yaml" ]; then
    echo "✓ taxonomy/recruiter/qna.yaml found"
else
    echo "✗ taxonomy/recruiter/qna.yaml NOT FOUND"
    echo "  Create this file before generating data"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Verify taxonomy files exist"
echo "2. Run: ilab data generate"
echo "3. Run: ilab model train"
echo ""
