#!/bin/bash
# 数据库迁移脚本 - 添加 reviewed_by_name 字段
# Database migration script - Add reviewed_by_name field

echo "🔄 Starting database migration..."

# 检查是否在 Docker 环境中
if [ -f /.dockerenv ]; then
    echo "📦 Running in Docker environment"
    python add_reviewed_by_name.py
else
    echo "💻 Running in local environment"
    
    # 检查是否有虚拟环境
    if [ -d "venv" ]; then
        echo "🐍 Activating virtual environment..."
        source venv/bin/activate
    fi
    
    python add_reviewed_by_name.py
fi

echo "✅ Migration completed!"
