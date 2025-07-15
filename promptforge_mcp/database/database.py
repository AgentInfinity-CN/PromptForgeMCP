#!/usr/bin/env python3
"""
数据库管理模块
提供SQLite数据库操作功能
"""

import json
import sqlite3
from typing import List, Optional
from promptforge_mcp.models.models import SavedPrompt


class DatabaseManager:
    """数据库管理器"""
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建提示库表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saved_prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                description TEXT DEFAULT '',
                category TEXT DEFAULT 'General',
                tags TEXT DEFAULT '[]',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                usage_count INTEGER DEFAULT 0
            )
        """)
        
        # 创建执行历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT NOT NULL,
                model TEXT NOT NULL,
                temperature REAL NOT NULL,
                max_tokens INTEGER,
                success BOOLEAN NOT NULL,
                response TEXT,
                error_msg TEXT,
                execution_time REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_prompt(self, title: str, content: str, description: str = "", 
                   category: str = "General", tags: List[str] = None) -> SavedPrompt:
        """保存提示"""
        if tags is None:
            tags = []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO saved_prompts (title, content, description, category, tags)
            VALUES (?, ?, ?, ?, ?)
        """, (title, content, description, category, json.dumps(tags)))
        
        prompt_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return self.get_prompt(prompt_id)
    
    def get_prompt(self, prompt_id: int) -> Optional[SavedPrompt]:
        """获取提示"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM saved_prompts WHERE id = ?", (prompt_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return SavedPrompt(
                id=row[0], title=row[1], content=row[2], description=row[3],
                category=row[4], tags=json.loads(row[5]), created_at=row[6],
                updated_at=row[7], usage_count=row[8]
            )
        return None
    
    def search_prompts(self, query: str = "", category: str = "", 
                      tags: List[str] = None, limit: int = 20) -> List[SavedPrompt]:
        """搜索提示"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        where_conditions = []
        params = []
        
        if query:
            where_conditions.append("(title LIKE ? OR content LIKE ? OR description LIKE ?)")
            query_param = f"%{query}%"
            params.extend([query_param, query_param, query_param])
        
        if category:
            where_conditions.append("category = ?")
            params.append(category)
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        cursor.execute(f"""
            SELECT * FROM saved_prompts 
            WHERE {where_clause}
            ORDER BY updated_at DESC 
            LIMIT ?
        """, params + [limit])
        
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            # 标签过滤
            prompt_tags = json.loads(row[5])
            if tags and not any(tag in prompt_tags for tag in tags):
                continue
                
            results.append(SavedPrompt(
                id=row[0], title=row[1], content=row[2], description=row[3],
                category=row[4], tags=prompt_tags, created_at=row[6],
                updated_at=row[7], usage_count=row[8]
            ))
        
        return results
    
    def delete_prompt(self, prompt_id: int) -> bool:
        """删除提示"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM saved_prompts WHERE id = ?", (prompt_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted 