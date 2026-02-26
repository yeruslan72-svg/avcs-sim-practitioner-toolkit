import sqlite3
import pandas as pd
from datetime import datetime
import json
import os

DB_PATH = "data/avcs_audits.db"

def init_db():
    """Создаёт таблицы, если их нет"""
    os.makedirs("data", exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS audits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            audit_date TEXT NOT NULL,
            practitioner_name TEXT NOT NULL,
            company_name TEXT,
            location TEXT,
            total_score REAL,
            classification TEXT,
            scores_json TEXT NOT NULL,
            respondents_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def save_audit(practitioner_name, company_name, location, total_score, classification, scores_dict, respondents_list):
    """Сохраняет завершённый аудит в базу"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        audit_date = datetime.now().strftime("%Y-%m-%d")
        scores_json = json.dumps(scores_dict)
        respondents_json = json.dumps(respondents_list, default=str)
        
        c.execute('''
            INSERT INTO audits 
            (audit_date, practitioner_name, company_name, location, total_score, classification, scores_json, respondents_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (audit_date, practitioner_name, company_name, location, total_score, classification, scores_json, respondents_json))
        
        conn.commit()
        audit_id = c.lastrowid
        conn.close()
        return audit_id
    except Exception as e:
        print(f"Error saving audit: {e}")
        return None

def get_audit_history(practitioner_name=None, limit=50):
    """Возвращает историю аудитов"""
    try:
        conn = sqlite3.connect(DB_PATH)
        
        if practitioner_name:
            query = "SELECT * FROM audits WHERE practitioner_name = ? ORDER BY created_at DESC LIMIT ?"
            df = pd.read_sql_query(query, conn, params=(practitioner_name, limit))
        else:
            query = "SELECT * FROM audits ORDER BY created_at DESC LIMIT ?"
            df = pd.read_sql_query(query, conn, params=(limit,))
        
        conn.close()
        return df
    except Exception as e:
        print(f"Error getting history: {e}")
        return pd.DataFrame()

def get_audit_by_id(audit_id):
    """Загружает конкретный аудит по ID"""
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM audits WHERE id = ?", conn, params=(audit_id,))
        conn.close()
        
        if len(df) == 0:
            return None
        
        row = df.iloc[0]
        return {
            'id': row['id'],
            'audit_date': row['audit_date'],
            'practitioner_name': row['practitioner_name'],
            'company_name': row['company_name'],
            'location': row['location'],
            'total_score': row['total_score'],
            'classification': row['classification'],
            'scores': json.loads(row['scores_json']),
            'respondents': json.loads(row['respondents_json']),
            'created_at': row['created_at']
        }
    except Exception as e:
        print(f"Error getting audit by id: {e}")
        return None

def delete_audit(audit_id):
    """Удаляет аудит"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM audits WHERE id = ?", (audit_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting audit: {e}")
        return False

def get_company_list():
    """Возвращает список уникальных компаний для фильтра"""
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT DISTINCT company_name FROM audits WHERE company_name IS NOT NULL ORDER BY company_name", conn)
        conn.close()
        return df['company_name'].tolist()
    except Exception as e:
        print(f"Error getting company list: {e}")
        return []
