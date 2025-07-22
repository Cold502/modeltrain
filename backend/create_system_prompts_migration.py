"""
数据库迁移脚本 - 更新SystemPrompt表结构
"""

import sqlite3
import os
from datetime import datetime

def migrate_system_prompts():
    """更新SystemPrompt表结构"""
    db_path = "app.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='system_prompts'
        """)
        
        if not cursor.fetchone():
            print("system_prompts表不存在，创建新表...")
            create_system_prompts_table(cursor)
        else:
            print("system_prompts表已存在，检查并添加新字段...")
            update_system_prompts_table(cursor)
        
        # 插入预定义系统提示词
        insert_predefined_prompts(cursor)
        
        conn.commit()
        print("数据库迁移完成！")
        
    except Exception as e:
        print(f"迁移失败: {e}")
        conn.rollback()
    finally:
        conn.close()

def create_system_prompts_table(cursor):
    """创建system_prompts表"""
    cursor.execute("""
        CREATE TABLE system_prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            content TEXT NOT NULL,
            description TEXT,
            format_type VARCHAR(50) DEFAULT 'openai',
            category VARCHAR(100) DEFAULT 'general',
            is_default BOOLEAN DEFAULT FALSE,
            is_system BOOLEAN DEFAULT FALSE,
            created_by INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    """)

def update_system_prompts_table(cursor):
    """更新已存在的system_prompts表"""
    # 获取现有列
    cursor.execute("PRAGMA table_info(system_prompts)")
    existing_columns = [column[1] for column in cursor.fetchall()]
    
    # 需要添加的新列
    new_columns = [
        ("description", "TEXT"),
        ("format_type", "VARCHAR(50) DEFAULT 'openai'"),
        ("category", "VARCHAR(100) DEFAULT 'general'"),
        ("is_system", "BOOLEAN DEFAULT FALSE")
    ]
    
    # 添加缺失的列
    for column_name, column_def in new_columns:
        if column_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE system_prompts ADD COLUMN {column_name} {column_def}")
                print(f"添加列: {column_name}")
            except Exception as e:
                print(f"添加列 {column_name} 失败: {e}")

def insert_predefined_prompts(cursor):
    """插入预定义系统提示词"""
    predefined_prompts = [
        {
            "name": "通用助手",
            "content": "你是一个有用、无害、诚实的AI助手。请根据用户的问题提供准确、有用的回答。",
            "description": "一个有用、无害、诚实的AI助手",
            "format_type": "openai",
            "category": "general",
            "is_system": True
        },
        {
            "name": "编程助手",
            "content": "你是一个专业的编程助手。你擅长多种编程语言，包括Python、JavaScript、Java、C++等。请为用户提供准确的代码建议、调试帮助和技术解决方案。在回答时，请提供清晰的代码示例和详细的解释。",
            "description": "专业的编程和技术问题助手",
            "format_type": "openai",
            "category": "coding",
            "is_system": True
        },
        {
            "name": "翻译助手",
            "content": "你是一个专业的翻译助手。你能够准确地在中文、英文、日文、韩文、法文、德文、西班牙文等多种语言之间进行翻译。请保持翻译的准确性和自然性，同时考虑文化背景和语境。",
            "description": "多语言翻译专家",
            "format_type": "openai",
            "category": "translation",
            "is_system": True
        },
        {
            "name": "创意写作助手",
            "content": "你是一个富有创意的写作助手。你擅长创作故事、诗歌、广告文案、营销内容等各种文体。请发挥你的想象力和创造力，为用户提供原创、有趣、引人入胜的内容。",
            "description": "创意写作和文案创作专家",
            "format_type": "openai",
            "category": "creative",
            "is_system": True
        }
    ]
    
    for prompt in predefined_prompts:
        # 检查是否已存在
        cursor.execute(
            "SELECT id FROM system_prompts WHERE name = ? AND is_system = TRUE",
            (prompt["name"],)
        )
        
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO system_prompts 
                (name, content, description, format_type, category, is_system, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                prompt["name"],
                prompt["content"],
                prompt["description"],
                prompt["format_type"],
                prompt["category"],
                prompt["is_system"],
                1  # 系统用户ID
            ))
            print(f"插入预定义提示词: {prompt['name']}")

if __name__ == "__main__":
    migrate_system_prompts() 