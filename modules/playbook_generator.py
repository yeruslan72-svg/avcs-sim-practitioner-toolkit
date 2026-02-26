import streamlit as st
from datetime import datetime

def generate_playbook(aggregated_scores, disagreements, company_name, location):
    """
    Генерирует персонализированный план действий на основе результатов аудита.
    """
    # Проверяем, что данные не None
    if aggregated_scores is None:
        aggregated_scores = {}
    
    # Безопасно получаем общий скор
    total_score = 0
    if aggregated_scores:
        for pillar, vals in aggregated_scores.items():
            if isinstance(vals, dict) and 'avg' in vals:
                total_score += vals['avg']
    
    playbook = {
        'company': company_name or "Unknown Company",
        'location': location or "Unknown Location",
        'date': datetime.now().strftime("%Y-%m-%d"),
        'total_score': total_score,
        'priority_areas': [],
        'quick_wins': [],
        'structural_recommendations': [],
        'disagreement_actions': []
    }
    
    # Определяем приоритетные области (самые низкие средние оценки)
    low_scores = []
    if aggregated_scores:
        for pillar, vals in aggregated_scores.items():
            if isinstance(vals, dict) and 'avg' in vals:
                if vals['avg'] <= 2.5:
                    low_scores.append((pillar, vals['avg']))
    
    low_scores.sort(key=lambda x: x[1])  # Сортируем от самых низких
    
    for pillar, score in low_scores:
        playbook['priority_areas'].append({
            'pillar': pillar.replace('_', ' ').title(),
            'score': f"{score:.1f}/5",
            'actions': get_actions_for_pillar(pillar, score)
        })
    
    # Быстрые победы (области с большими расхождениями)
    if disagreements:
        for d in disagreements:
            if isinstance(d, dict):
                playbook['disagreement_actions'].append({
                    'pillar': d.get('pillar', 'Unknown'),
                    'spread': f"{d.get('spread', 0):.1f} points",
                    'action': f"Conduct focused workshop with {d.get('min', 0)}-scoring and {d.get('max', 0)}-scoring respondents to align understanding"
                })
    
    # Общие структурные рекомендации
    playbook['structural_recommendations'] = get_structural_recommendations(aggregated_scores)
    
    return playbook

def get_actions_for_pillar(pillar, score):
    """Возвращает конкретные действия для каждого Pillar в зависимости от оценки"""
    
    actions = {
        'trigger_clarity': [
            "Review and document all critical deviation thresholds",
            "Ensure thresholds are quantitative, not qualitative",
            "Implement automatic escalation for thresholds exceeded",
            "Train all operators on mandatory vs interpretive triggers",
            "Audit last 3 months of logs for unreported deviations"
        ],
        'decision_ownership': [
            "Define single accountable owner for each critical decision type",
            "Update job descriptions to include decision authority",
            "Ensure owners are operationally present 24/7",
            "Create escalation matrix with clear ownership levels",
            "Review last 3 incidents for ownership diffusion"
        ],
        'protected_intervention': [
            "Formally codify stop-work authority in policy",
            "Remove stop-work events from KPI calculations",
            "Train supervisors to respond positively to stops",
            "Create 'positive stop' recognition program",
            "Review last 6 months of stop events for retaliation"
        ],
        'override_transparency': [
            "Implement mandatory override logging system",
            "Require named approver for all overrides",
            "Create weekly override review meetings",
            "Analyze override patterns for systemic issues",
            "Audit undocumented workarounds in key processes"
        ],
        'drift_detection': [
            "Implement trend analysis for all minor deviations",
            "Create monthly drift report for management",
            "Set up alerts for repeated small deviations",
            "Review last 12 months of deviation logs for patterns",
            "Assign ownership for drift monitoring"
        ]
    }
    
    # Возвращаем действия, адаптированные под уровень скора
    pillar_actions = actions.get(pillar, [])
    if score <= 1.5:
        return pillar_actions  # Все действия
    elif score <= 2.5:
        return pillar_actions[:3]  # Топ-3 действия
    else:
        return pillar_actions[:2]  # Топ-2 действия

def get_structural_recommendations(aggregated_scores):
    """Возвращает общие структурные рекомендации"""
    
    recommendations = []
    
    # Анализ по каждому Pillar, если данные есть
    if aggregated_scores:
        if aggregated_scores.get('trigger_clarity', {}).get('avg', 5) < 3:
            recommendations.append("Establish a formal 'Deviation Review Board' to analyze all threshold exceedances")
        
        if aggregated_scores.get('decision_ownership', {}).get('avg', 5) < 3:
            recommendations.append("Create a Decision Rights Matrix (RAPID or similar) for all critical operations")
        
        if aggregated_scores.get('protected_intervention', {}).get('avg', 5) < 3:
            recommendations.append("Implement a 'Safety Pause' program with guaranteed protection for those who stop work")
        
        if aggregated_scores.get('override_transparency', {}).get('avg', 5) < 3:
            recommendations.append("Deploy a digital override tracking system with automated alerts to management")
        
        if aggregated_scores.get('drift_detection', {}).get('avg', 5) < 3:
            recommendations.append("Establish a 'Drift Dashboard' showing trends in minor deviations over time")
    
    # Добавляем общие рекомендации
    recommendations.append("Schedule a follow-up SIM assessment in 6 months to measure progress")
    recommendations.append("Share aggregated results with all respondents to close the feedback loop")
    
    return recommendations

def format_playbook_for_display(playbook):
    """Форматирует playbook для отображения в Streamlit"""
    
    md = f"""
    ## 📋 AVCS Structural Integrity Playbook
    
    **Company:** {playbook['company']}  
    **Location:** {playbook['location']}  
    **Date:** {playbook['date']}  
    **Total Score:** {playbook['total_score']:.1f}/25
    
    ---
    """
    
    if playbook['priority_areas']:
        md += "\n### 🔴 Priority Areas (Lowest Scores)\n"
        for area in playbook['priority_areas']:
            md += f"\n#### {area['pillar']} — {area['score']}\n"
            for action in area['actions']:
                md += f"- [ ] {action}\n"
    
    if playbook['disagreement_actions']:
        md += "\n### ⚠️ Alignment Opportunities\n"
        md += "*Areas where respondents disagree — conduct focused workshops*\n\n"
        for item in playbook['disagreement_actions']:
            md += f"- **{item['pillar']}** (spread {item['spread']}): {item['action']}\n"
    
    if playbook['structural_recommendations']:
        md += "\n### 🏗️ Structural Recommendations\n"
        for rec in playbook['structural_recommendations']:
            md += f"- {rec}\n"
    
    return md

def export_playbook_to_markdown(playbook):
    """Экспортирует playbook в Markdown для скачивания"""
    return format_playbook_for_display(playbook)
