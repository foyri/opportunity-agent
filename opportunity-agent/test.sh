#!/bin/bash
# Test script for Opportunity Matching Agent

echo "🧪 Testing Opportunity Matching Agent"
echo "======================================"

# Test 1: Import all modules
echo -e "\n📦 Test 1: Module imports..."
python3 -c "from skills.fetch import OpportunityFetcher; from skills.score import OpportunityScorer; from skills.act import OpportunityActor; print('✅ All modules import successfully')" || exit 1

# Test 2: Config loading
echo -e "\n⚙️  Test 2: Configuration..."
python3 -c "import json; c=json.load(open('config.json')); print(f\"✅ Config loaded: {c['profile']['name']}\")" || exit 1

# Test 3: Database initialization
echo -e "\n🗄️  Test 3: Database..."
rm -f data/test.db
python3 -c "
import sqlite3
conn = sqlite3.connect('data/test.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS test (id TEXT PRIMARY KEY)')
conn.commit()
conn.close()
print('✅ Database works')
" || exit 1
rm -f data/test.db

# Test 4: V2EX fetch
echo -e "\n📡 Test 4: V2EX RSS fetch..."
python3 -c "
from skills.fetch import OpportunityFetcher
import json
with open('config.json') as f:
    config = json.load(f)
fetcher = OpportunityFetcher(config)
ops = fetcher._fetch_v2ex()
print(f'✅ Fetched {len(ops)} opportunities from V2EX')
" || exit 1

# Test 5: Scoring pipeline
echo -e "\n🧠 Test 5: Scoring pipeline..."
python3 -c "
from skills.fetch import OpportunityFetcher
from skills.score import OpportunityScorer
import json
with open('config.json') as f:
    config = json.load(f)
fetcher = OpportunityFetcher(config)
scorer = OpportunityScorer(config)
ops = fetcher._fetch_v2ex()[:3]
results = scorer.score_batch(ops)
print(f'✅ Scored {len(results)} opportunities')
for r in results[:2]:
    print(f'   - {r[\"title\"][:40]}... → Score: {r[\"score\"]}')
" || exit 1

# Test 6: Full pipeline (dry run)
echo -e "\n🔄 Test 6: Full pipeline (dry run)..."
rm -f data/opportunities.db
python3 run.py 2>&1 | grep -E "(Found|Processed|Done)" && echo "✅ Full pipeline works" || exit 1

echo -e "\n======================================"
echo "✅ All tests passed!"
echo ""
echo "Next steps:"
echo "  1. Add API credentials to config.json for 猎聘/智联"
echo "  2. Set up cron: crontab -e"
echo "  3. Add line: 0 8 * * * cd $(pwd) && python3 run.py"
