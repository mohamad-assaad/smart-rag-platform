# Environment variables
.env
.env.*
!.env.example

# Python virtual environments
.venv/
venv/
env/

# Python cache
__pycache__/
*.py[cod]
*$py.class

# Python build files
build/
dist/
*.egg-info/
.eggs/

# Pytest / coverage
.pytest_cache/
.coverage
htmlcov/

# IDE / editor
.vscode/
.idea/

# OS files
.DS_Store
Thumbs.db

# Docker / local data
*.log

# Local database files
*.sqlite
*.sqlite3

# Temporary files
tmp/
temp/

# Qdrant / local storage if created outside Docker volume
qdrant_storage/

# Redis dumps if created locally
dump.rdb