#!/bin/bash
# Quick script to update rankings and rebuild HTML

echo "🏓 Pickleball League Rankings Update"
echo "===================================="
echo ""

# Step 1: Generate rankings
echo "📊 Calculating rankings from match data..."
python3 scripts/generate_rankings.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Rankings calculated successfully!"
    echo ""

    # Step 2: Build HTML pages
    echo "🌐 Generating HTML pages..."
    python3 scripts/build_pages.py

    if [ $? -eq 0 ]; then
        echo ""
        echo "✓ All done! Open index.html to view the rankings."
        echo ""

        # Optional: Open in browser (macOS)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo "Opening in browser..."
            open index.html
        fi
    else
        echo "❌ Error generating HTML pages"
        exit 1
    fi
else
    echo "❌ Error calculating rankings"
    exit 1
fi
