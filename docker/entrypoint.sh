#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Settlement Monitoring Data Platform${NC}"
echo -e "${GREEN}========================================${NC}"

# Step 1: Wait for PostgreSQL to be ready
echo -e "\n${YELLOW}[Step 1] Waiting for PostgreSQL${NC}"
until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; do
  echo "  Waiting for PostgreSQL to be ready..."
  sleep 2
done
echo -e "${GREEN}[OK] PostgreSQL is ready.${NC}"

# Step 2: Initialize the database schema
echo -e "\n${YELLOW}[Step 2] Initializing database schema${NC}"
PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -f sql/init_database.sql
echo -e "${GREEN}[OK] Database schema initialized.${NC}"

# Step 3: Run the full data pipeline
echo -e "\n${YELLOW}[Step 3] Running data pipeline${NC}"
python main.py

# Step 4: Show results
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}   Pipeline completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\nOutput files can be found in:"
echo -e "  ${YELLOW}output/figures/${NC}         - Visualization charts"
echo -e "  ${YELLOW}output/reports/${NC}         - Data quality reports"
echo -e "  ${YELLOW}output/training/${NC}        - Training datasets (JSONL)"
echo -e "\nTo run a specific module, use:"
echo -e "  docker compose run --rm app python -m src.<module_name>"
echo -e "  Example: docker compose run --rm app python -m src.analysis"
