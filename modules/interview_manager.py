import pandas as pd
import streamlit as st

def init_interview_state():
    """Инициализация состояния для множественных интервью"""
    if 'respondents' not in st.session_state:
        st.session_state.respondents = []
    if 'current_respondent' not in st.session_state:
        st.session_state.current_respondent = {}
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    if 'edit_index' not in st.session_state:
        st.session_state.edit_index = None

def add_respondent(name, role, answers, scores):
    """Добавить нового респондента с защитой от ошибок"""
    # Проверяем, что scores — это словарь
    if scores is None or not isinstance(scores, dict):
        scores = {
            'trigger_clarity': 0,
            'decision_ownership': 0,
            'protected_intervention': 0,
            'override_transparency': 0,
            'drift_detection': 0
        }
    
    # Проверяем, что answers — это словарь
    if answers is None or not isinstance(answers, dict):
        answers = {}
    
    respondent = {
        'name': name,
        'role': role,
        'answers': answers.copy(),
        'scores': scores.copy(),
        'timestamp': pd.Timestamp.now()
    }
    st.session_state.respondents.append(respondent)

def update_respondent(index, name, role, answers, scores):
    """Обновить существующего респондента с защитой"""
    if 0 <= index < len(st.session_state.respondents):
        # Проверяем, что scores — это словарь
        if scores is None or not isinstance(scores, dict):
            scores = {
                'trigger_clarity': 0,
                'decision_ownership': 0,
                'protected_intervention': 0,
                'override_transparency': 0,
                'drift_detection': 0
            }
        
        # Проверяем, что answers — это словарь
        if answers is None or not isinstance(answers, dict):
            answers = {}
        
        st.session_state.respondents[index] = {
            'name': name,
            'role': role,
            'answers': answers.copy(),
            'scores': scores.copy(),
            'timestamp': pd.Timestamp.now()
        }

def delete_respondent(index):
    """Удалить респондента"""
    if 0 <= index < len(st.session_state.respondents):
        del st.session_state.respondents[index]

def get_aggregated_scores():
    """Получить агрегированные scores по всем респондентам"""
    if not st.session_state.respondents:
        return None
    
    scores_list = [r['scores'] for r in st.session_state.respondents]
    
    aggregated = {
        'trigger_clarity': {
            'avg': sum(s['trigger_clarity'] for s in scores_list) / len(scores_list),
            'min': min(s['trigger_clarity'] for s in scores_list),
            'max': max(s['trigger_clarity'] for s in scores_list)
        },
        'decision_ownership': {
            'avg': sum(s['decision_ownership'] for s in scores_list) / len(scores_list),
            'min': min(s['decision_ownership'] for s in scores_list),
            'max': max(s['decision_ownership'] for s in scores_list)
        },
        'protected_intervention': {
            'avg': sum(s['protected_intervention'] for s in scores_list) / len(scores_list),
            'min': min(s['protected_intervention'] for s in scores_list),
            'max': max(s['protected_intervention'] for s in scores_list)
        },
        'override_transparency': {
            'avg': sum(s['override_transparency'] for s in scores_list) / len(scores_list),
            'min': min(s['override_transparency'] for s in scores_list),
            'max': max(s['override_transparency'] for s in scores_list)
        },
        'drift_detection': {
            'avg': sum(s['drift_detection'] for s in scores_list) / len(scores_list),
            'min': min(s['drift_detection'] for s in scores_list),
            'max': max(s['drift_detection'] for s in scores_list)
        }
    }
    
    return aggregated

def get_consensus_score():
    """Получить общий скор (среднее от агрегированных)"""
    agg = get_aggregated_scores()
    if not agg:
        return 0
    total = (agg['trigger_clarity']['avg'] +
             agg['decision_ownership']['avg'] +
             agg['protected_intervention']['avg'] +
             agg['override_transparency']['avg'] +
             agg['drift_detection']['avg'])
    return total

def get_disagreement_areas(threshold=1.5):
    """Найти области наибольшего расхождения (max - min > threshold)"""
    agg = get_aggregated_scores()
    if not agg:
        return []
    
    disagreements = []
    for pillar, values in agg.items():
        spread = values['max'] - values['min']
        if spread > threshold:
            disagreements.append({
                'pillar': pillar.replace('_', ' ').title(),
                'spread': spread,
                'min': values['min'],
                'max': values['max']
            })
    
    return sorted(disagreements, key=lambda x: x['spread'], reverse=True)
