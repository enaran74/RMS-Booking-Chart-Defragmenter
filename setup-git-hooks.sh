#!/bin/bash
#
# Setup Git hooks for automatic version management
# Run this once after cloning the repository
#

set -e

echo "🔧 Setting up Git hooks for version management..."

# Create hooks directory if it doesn't exist
mkdir -p .git/hooks

# Install the pre-commit hook
if [ -f .githooks/pre-commit ]; then
    cp .githooks/pre-commit .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
    echo "✅ Pre-commit hook installed"
else
    echo "❌ Error: .githooks/pre-commit not found"
    exit 1
fi

# Test the hook
echo "🧪 Testing pre-commit hook..."
if .git/hooks/pre-commit; then
    echo "✅ Pre-commit hook test successful"
else
    echo "⚠️  Pre-commit hook test had issues (but hook is installed)"
fi

echo ""
echo "🎉 Git hooks setup complete!"
echo ""
echo "📋 Usage:"
echo "  • Version badges in README.md will auto-update on each commit"
echo "  • Create release tags with: git tag v1.2.3 && git push origin v1.2.3"
echo "  • Development versions show as: v1.2.3-5-abc1234"
echo "  • Production releases show as: v1.2.3"
echo ""
