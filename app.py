import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import base64
from datetime import datetime

# ------------------------------
# Конфигурация страницы — САМАЯ ПЕРВАЯ
# ------------------------------
st.set_page_config(
    page_title="AVCS SIM - Practitioner Toolkit",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ------------------------------
# Импорт модулей
# ------------------------------
from modules.auth import check_authentication
from modules.interview_manager import (
    init_interview_state, add_respondent, update_respondent, delete_respondent,
    get_aggregated_scores, get_consensus_score, get_disagreement_areas
)
from modules.database import init_db, save_audit, get_audit_history, get_audit_by_id, delete_audit, get_company_list
from modules.playbook_generator import generate_playbook, format_playbook_for_display, export_playbook_to_markdown

# ------------------------------
# Инициализация БД
# ------------------------------
init_db()

# ------------------------------
# Проверка аутентификации
# ------------------------------
name, authentication_status, username, authenticator = check_authentication()

if authentication_status == False:
    st.error("Username/password is incorrect")
    st.stop()

if authentication_status == None:
    st.warning("Please enter your credentials")
    st.stop()

# ------------------------------
# Инициализация состояния
# ------------------------------
init_interview_state()

if 'step' not in st.session_state:
    st.session_state.step = 1
if 'scores' not in st.session_state:
    st.session_state.scores = {
        'trigger_clarity': 0,
        'decision_ownership': 0,
        'protected_intervention': 0,
        'override_transparency': 0,
        'drift_detection': 0
    }
if 'answers' not in st.session_state:
    st.session_state.answers = {}
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'new'  # 'new' or 'history'
if 'selected_audit' not in st.session_state:
    st.session_state.selected_audit = None
if 'show_playbook' not in st.session_state:
    st.session_state.show_playbook = False
if 'last_aggregated' not in st.session_state:
    st.session_state.last_aggregated = None
if 'last_disagreements' not in st.session_state:
    st.session_state.last_disagreements = None

# ------------------------------
# Стили CSS
# ------------------------------
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    .main-header {
        text-align: center; padding: 20px 0;
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white; border-radius: 10px; margin-bottom: 20px;
    }
    .pillar-card {
        background-color: white; color: #000000; padding: 20px;
        border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 15px; border-left: 4px solid #1e3a8a;
    }
    .score-box {
        background-color: #1e3a8a; color: white; padding: 20px;
        border-radius: 10px; text-align: center; font-size: 48px;
        font-weight: bold; margin: 15px 0;
    }
    .audit-card {
        background-color: white; padding: 15px; border-radius: 10px;
        margin-bottom: 10px; border-left: 4px solid #3b82f6;
        cursor: pointer;
    }
    .audit-card:hover {
        background-color: #f0f2f6;
    }
    .playbook-section {
        background-color: #e8f0fe; padding: 20px; border-radius: 10px;
        margin: 20px 0; border-left: 4px solid #1e3a8a;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------
# Боковая панель
# ------------------------------
with st.sidebar:
    st.image("logo.png", width=200)
    st.markdown(f"**Welcome, {name}!**")
    if authenticator:
        authenticator.logout('Logout', 'main')
    
    st.markdown("---")
    
    # Навигация
    if st.button("➕ New Audit", use_container_width=True):
        st.session_state.view_mode = 'new'
        st.session_state.step = 1
        st.session_state.show_playbook = False
        st.rerun()
    
    if st.button("📋 Audit History", use_container_width=True):
        st.session_state.view_mode = 'history'
        st.session_state.step = 1
        st.session_state.show_playbook = False
        st.rerun()
    
    st.markdown("---")
    
    if st.session_state.view_mode == 'new':
        st.markdown(f"**Respondents:** {len(st.session_state.respondents)}")
        
        if st.session_state.respondents:
            st.markdown("### Respondent List")
            for i, resp in enumerate(st.session_state.respondents):
                with st.expander(f"{resp['role']}: {resp['name']}"):
                    st.write(f"Trigger: {resp['scores']['trigger_clarity']}/5")
                    st.write(f"Ownership: {resp['scores']['decision_ownership']}/5")
                    st.write(f"Intervention: {resp['scores']['protected_intervention']}/5")
                    st.write(f"Override: {resp['scores']['override_transparency']}/5")
                    st.write(f"Drift: {resp['scores']['drift_detection']}/5")
                    if st.button(f"Delete", key=f"del_{i}"):
                        delete_respondent(i)
                        st.rerun()
        
        st.markdown("---")
        st.markdown("## Progress")
        step = st.session_state.step
        progress = (step - 1) / 6
        if progress < 0:
            progress = 0.0
        elif progress > 1:
            progress = 1.0
        st.progress(progress)
        st.markdown(f"**Step {step} of 6**")

# ------------------------------
# Заголовок
# ------------------------------
if st.session_state.view_mode == 'new':
    st.markdown("""
    <div class="main-header">
        <h1>🧭 AVCS Structural Integrity Module</h1>
        <p>Practitioner Toolkit — New Audit</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="main-header">
        <h1>📋 Audit History</h1>
        <p>View and manage past audits</p>
    </div>
    """, unsafe_allow_html=True)

# ------------------------------
# Функции расчёта
# ------------------------------
def calculate_trigger_score(answers):
    score = 0
    if answers.get('q1_1') == "Yes, mandatory and enforced": score += 2
    elif answers.get('q1_1') == "Yes, but discretionary": score += 1
    if answers.get('q1_2') == "No, all deviations tracked": score += 2
    elif answers.get('q1_2') == "Sometimes noticed": score += 1
    if answers.get('q1_3') == "Automatic": score += 1
    return min(score, 5)

def calculate_ownership_score(answers):
    score = 0
    if answers.get('q2_1') == "Yes, singular owner defined": score += 2
    elif answers.get('q2_1') == "Shared but clear": score += 1
    if answers.get('q2_2') == "Yes, always present": score += 2
    elif answers.get('q2_2') == "Usually present": score += 1
    if answers.get('q2_3') == "No, never": score += 1
    return min(score, 5)

def calculate_intervention_score(answers):
    score = 0
    if answers.get('q3_1') == "Yes, formally codified and protected": score += 2
    elif answers.get('q3_1') == "Yes, but informally": score += 1
    if answers.get('q3_2') == "Always supported": score += 2
    elif answers.get('q3_2') == "Usually supported": score += 1
    if answers.get('q3_3') == "No, never": score += 1
    return min(score, 5)

def calculate_override_score(answers):
    score = 0
    if answers.get('q4_1') == "No, always documented": score += 2
    elif answers.get('q4_1') == "Sometimes documented": score += 1
    if answers.get('q4_2') == "Yes, always": score += 2
    elif answers.get('q4_2') == "Sometimes": score += 1
    if answers.get('q4_3') == "Yes, regularly": score += 1
    return min(score, 5)

def calculate_drift_score(answers):
    score = 0
    if answers.get('q5_1') == "Yes, systematically": score += 2
    elif answers.get('q5_1') == "Sometimes": score += 1
    if answers.get('q5_2') == "Yes, regularly": score += 2
    elif answers.get('q5_2') == "Occasionally": score += 1
    if answers.get('q5_3') == "Yes, actively": score += 1
    return min(score, 5)

# ------------------------------
# Функция для радара
# ------------------------------
def create_radar_chart(scores_dict):
    categories = ['Trigger Clarity', 'Decision Ownership', 'Protected Intervention',
                  'Override Transparency', 'Drift Detection']
    values = [scores_dict[p] for p in ['trigger_clarity','decision_ownership',
                                        'protected_intervention','override_transparency',
                                        'drift_detection']]
    fig = go.Figure(data=go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill='toself', line_color='#1e3a8a',
        fillcolor='rgba(30,58,138,0.3)'
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0,5])),
        showlegend=False, height=400,
        margin=dict(l=80, r=80, t=20, b=20)
    )
    return fig

# ------------------------------
# Функция для PDF
# ------------------------------
def create_pdf(scores, total_score, company="", location=""):
    pdf = FPDF()
    pdf.add_page()
    
    try:
        pdf.image("logo.png", x=10, y=8, w=30)
        pdf.ln(15)
    except:
        pdf.ln(10)
    
    pdf.set_font('Arial','B',16)
    pdf.cell(0,10,'AVCS Structural Integrity Module Report',0,1,'C')
    pdf.ln(10)
    
    pdf.set_font('Arial','',10)
    pdf.cell(0,10,f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}',0,1,'R')
    pdf.ln(5)
    
    pdf.set_font('Arial','I',10)
    pdf.cell(0,10,f'Certified AVCS Practitioner: {name} (ID: #001)',0,1,'L')
    if company:
        pdf.cell(0,10,f'Company: {company}',0,1,'L')
    if location:
        pdf.cell(0,10,f'Location: {location}',0,1,'L')
    pdf.ln(5)
    
    pdf.set_font('Arial','B',12)
    pdf.cell(0,10,f'Total Structural Integrity Score: {total_score:.1f} / 25',0,1)
    
    if total_score <= 10: cls = "HIGH STRUCTURAL VULNERABILITY"
    elif total_score <= 17: cls = "CONDITIONAL STABILITY"
    elif total_score <= 22: cls = "STRUCTURALLY CONTROLLED"
    else: cls = "ARCHITECTURALLY RESILIENT"
    
    pdf.set_font('Arial','B',12)
    pdf.cell(0,10,f'Classification: {cls}',0,1)
    pdf.ln(10)
    
    pdf.set_font('Arial','B',12)
    pdf.cell(0,10,'Pillar Scores:',0,1)
    pdf.set_font('Arial','',12)
    
    pillars = [
        ('Trigger Clarity', scores['trigger_clarity']),
        ('Decision Ownership', scores['decision_ownership']),
        ('Protected Intervention', scores['protected_intervention']),
        ('Override Transparency', scores['override_transparency']),
        ('Drift Detection', scores['drift_detection'])
    ]
    
    for p,s in pillars:
        pdf.cell(0,10,f'{p}: {s:.1f}/5',0,1)
    
    pdf.ln(10)
    
    pdf.set_y(-30)
    pdf.set_font('Arial','I',8)
    pdf.cell(0,10,'AVCS Structural Integrity Module',0,1,'C')
    pdf.cell(0,10,'© 2026 Yeruslan Chihachyov, Operational Excellence Delivered Consulting',0,1,'C')
    
    pdf_bytes = pdf.output()
    return base64.b64encode(pdf_bytes).decode('utf-8')

def cls_from_score(score):
    if score <= 10: return "HIGH STRUCTURAL VULNERABILITY"
    elif score <= 17: return "CONDITIONAL STABILITY"
    elif score <= 22: return "STRUCTURALLY CONTROLLED"
    else: return "ARCHITECTURALLY RESILIENT"

# ------------------------------
# Страница истории аудитов
# ------------------------------
if st.session_state.view_mode == 'history':
    if st.session_state.selected_audit is None:
        col1, col2 = st.columns([2,1])
        with col1:
            st.markdown("### Past Audits")
        with col2:
            company_filter = st.selectbox("Filter by company", ["All"] + get_company_list())
        
        df = get_audit_history(practitioner_name=name, limit=100)
        
        if len(df) == 0:
            st.info("No audits found. Start by creating a new audit.")
        else:
            for _, row in df.iterrows():
                with st.container():
                    cols = st.columns([3,1,1,1])
                    cols[0].markdown(f"**{row['audit_date']}** — {row['company_name'] or 'N/A'}")
                    cols[1].markdown(f"Score: {row['total_score']:.1f}/25")
                    cols[2].markdown(f"{row['classification']}")
                    if cols[3].button("View", key=f"view_{row['id']}"):
                        st.session_state.selected_audit = row['id']
                        st.rerun()
    else:
        audit = get_audit_by_id(st.session_state.selected_audit)
        if audit:
            st.markdown(f"## Audit from {audit['audit_date']}")
            st.markdown(f"**Company:** {audit['company_name'] or 'N/A'}  |  **Location:** {audit['location'] or 'N/A'}")
            st.markdown(f"**Practitioner:** {audit['practitioner_name']}")
            
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                st.markdown(f'<div class="score-box">{audit["total_score"]:.1f} / 25</div>', unsafe_allow_html=True)
                st.markdown(f"### {audit['classification']}")
            
            colA, colB = st.columns(2)
            with colA:
                st.markdown("### Scores")
                for pillar, score in audit['scores'].items():
                    st.markdown(f"**{pillar.replace('_',' ').title()}:** {score:.1f}/5")
            
            with colB:
                st.markdown("### Radar")
                fig = create_radar_chart(audit['scores'])
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("### Respondents")
            for r in audit['respondents']:
                st.markdown(f"- **{r['role']}:** {r['name']}")
            
            colX, colY, colZ = st.columns(3)
            with colX:
                if st.button("← Back to List"):
                    st.session_state.selected_audit = None
                    st.rerun()
            with colY:
                pdf_data = create_pdf(audit['scores'], audit['total_score'], audit['company_name'], audit['location'])
                href = f'<a href="data:application/octet-stream;base64,{pdf_data}" download="AVCS_Audit_{audit["id"]}.pdf"><button style="background-color:#1e3a8a; color:white; padding:8px 16px;">📥 Download PDF</button></a>'
                st.markdown(href, unsafe_allow_html=True)
            with colZ:
                if st.button("🗑️ Delete", type="primary"):
                    delete_audit(audit['id'])
                    st.session_state.selected_audit = None
                    st.rerun()
        else:
            st.error("Audit not found")
            if st.button("← Back to List"):
                st.session_state.selected_audit = None
                st.rerun()

# ------------------------------
# Основной интерфейс нового аудита
# ------------------------------
elif st.session_state.view_mode == 'new':
    
    if not st.session_state.edit_mode and st.session_state.step == 1:
        col1, col2 = st.columns([2,1])
        with col1:
            st.markdown("### Respondents")
            if st.session_state.respondents:
                for i, resp in enumerate(st.session_state.respondents):
                    with st.container():
                        cols = st.columns([3,1,1])
                        cols[0].markdown(f"**{resp['role']}:** {resp['name']}")
                        cols[1].markdown(f"Score: {sum(resp['scores'].values())}/25")
                        if cols[2].button("Edit", key=f"edit_{i}"):
                            st.session_state.edit_mode = True
                            st.session_state.edit_index = i
                            st.session_state.step = 2
                            st.rerun()
            else:
                st.info("No respondents yet. Add your first respondent below.")
        
        with col2:
            st.markdown("### Actions")
            if st.button("➕ New Respondent", use_container_width=True):
                st.session_state.edit_mode = False
                st.session_state.step = 2
                st.rerun()
            
            if st.session_state.respondents:
                if st.button("📊 Show Aggregated Results", use_container_width=True):
                    st.session_state.step = 7
                    st.rerun()

    elif st.session_state.step == 2:
        st.markdown("""
        <div class="pillar-card">
            <h2>1. Trigger Clarity</h2>
            <p>Are escalation conditions mandatory or interpretive?</p>
        </div>
        """, unsafe_allow_html=True)
        with st.form("trigger_form"):
            q1 = st.radio(
                "Are critical deviation thresholds mandatory and enforced, or discretionary?",
                ["Yes, mandatory and enforced","Yes, but discretionary","No clear thresholds"], key='q1_1'
            )
            q2 = st.radio(
                "Can deviations exist without crossing formal limits?",
                ["No, all deviations tracked","Sometimes noticed","Yes, often unnoticed"], key='q1_2'
            )
            q3 = st.radio(
                "Is escalation automatic or requires human decision?",
                ["Automatic","Requires decision","Often doesn't happen"], key='q1_3'
            )
            if st.form_submit_button("Next →"):
                st.session_state.answers.update(st.session_state)
                st.session_state.scores['trigger_clarity'] = calculate_trigger_score(st.session_state.answers)
                st.session_state.step = 3
                st.rerun()

    elif st.session_state.step == 3:
        st.markdown("""
        <div class="pillar-card">
            <h2>2. Decision Ownership</h2>
            <p>Is accountability singular and real-time?</p>
        </div>
        """, unsafe_allow_html=True)
        with st.form("ownership_form"):
            q1 = st.radio(
                "Is a single accountable owner defined for critical decisions?",
                ["Yes, singular owner defined","Shared but clear","Collective/unclear"], key='q2_1'
            )
            q2 = st.radio(
                "Is the owner operationally present during risk exposure?",
                ["Yes, always present","Usually present","Rarely present"], key='q2_2'
            )
            q3 = st.radio(
                "Can ownership be overridden collectively without traceability?",
                ["No, never","Sometimes","Yes, commonly"], key='q2_3'
            )
            if st.form_submit_button("Next →"):
                st.session_state.answers.update(st.session_state)
                st.session_state.scores['decision_ownership'] = calculate_ownership_score(st.session_state.answers)
                st.session_state.step = 4
                st.rerun()

    elif st.session_state.step == 4:
        st.markdown("""
        <div class="pillar-card">
            <h2>3. Protected Intervention</h2>
            <p>Is stopping operations structurally safe?</p>
        </div>
        """, unsafe_allow_html=True)
        with st.form("intervention_form"):
            q1 = st.radio(
                "Is stop-work authority formally codified and protected?",
                ["Yes, formally codified and protected","Yes, but informally","No"], key='q3_1'
            )
            q2 = st.radio(
                "How are stop-work decisions reviewed?",
                ["Always supported","Usually supported","Questioned/criticized"], key='q3_2'
            )
            q3 = st.radio(
                "Does stopping operations negatively affect performance metrics?",
                ["No, never","Sometimes","Yes, often"], key='q3_3'
            )
            if st.form_submit_button("Next →"):
                st.session_state.answers.update(st.session_state)
                st.session_state.scores['protected_intervention'] = calculate_intervention_score(st.session_state.answers)
                st.session_state.step = 5
                st.rerun()

    elif st.session_state.step == 5:
        st.markdown("""
        <div class="pillar-card">
            <h2>4. Override Transparency</h2>
            <p>Are deviations visible and traceable?</p>
        </div>
        """, unsafe_allow_html=True)
        with st.form("override_form"):
            q1 = st.radio(
                "Can procedures be bypassed informally without documentation?",
                ["No, always documented","Sometimes documented","Yes, commonly"], key='q4_1'
            )
            q2 = st.radio(
                "Are overrides traceable to a named decision-maker?",
                ["Yes, always","Sometimes","Rarely"], key='q4_2'
            )
            q3 = st.radio(
                "Are overrides reviewed periodically?",
                ["Yes, regularly","Occasionally","Never"], key='q4_3'
            )
            if st.form_submit_button("Next →"):
                st.session_state.answers.update(st.session_state)
                st.session_state.scores['override_transparency'] = calculate_override_score(st.session_state.answers)
                st.session_state.step = 6
                st.rerun()

    elif st.session_state.step == 6:
        st.markdown("""
        <div class="pillar-card">
            <h2>5. Drift Detection</h2>
            <p>Is boundary movement tracked or ignored?</p>
        </div>
        """, unsafe_allow_html=True)
        with st.form("drift_form"):
            q1 = st.radio(
                "Are minor deviations recorded systematically?",
                ["Yes, systematically","Sometimes","Rarely"], key='q5_1'
            )
            q2 = st.radio(
                "Is deviation trend analyzed longitudinally?",
                ["Yes, regularly","Occasionally","Never"], key='q5_2'
            )
            q3 = st.radio(
                "Is normalization of deviation actively monitored?",
                ["Yes, actively","Sometimes","No"], key='q5_3'
            )
            if st.form_submit_button("Calculate Results →"):
                st.session_state.answers.update(st.session_state)
                st.session_state.scores['drift_detection'] = calculate_drift_score(st.session_state.answers)
                st.session_state.step = 8
                st.rerun()

    elif st.session_state.step == 8:
        st.markdown("### Save Respondent")
        with st.form("save_respondent_form"):
            name_input = st.text_input("Name", value="", placeholder="e.g. John Smith")
            role_input = st.selectbox("Role", ["Operator","Supervisor","HSE","Manager","Other"])
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Save and Add Another"):
                    if name_input and role_input:
                        add_respondent(name_input, role_input, st.session_state.answers, st.session_state.scores)
                        for key in ['step','answers','scores']:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.rerun()
            with col2:
                if st.form_submit_button("Save and Show Summary"):
                    if name_input and role_input:
                        add_respondent(name_input, role_input, st.session_state.answers, st.session_state.scores)
                        for key in ['step','answers','scores']:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.session_state.step = 1
                        st.rerun()

    elif st.session_state.step == 7:
        agg = get_aggregated_scores()
        if not agg:
            st.warning("No respondents yet. Add at least one respondent to see results.")
            if st.button("← Back"):
                st.session_state.step = 1
                st.rerun()
        else:
            st.session_state.last_aggregated = agg
            st.session_state.last_disagreements = get_disagreement_areas()
            
            st.markdown("## Aggregated Results")
            
            total = get_consensus_score()
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                st.markdown(f'<div class="score-box">{total:.1f} / 25</div>', unsafe_allow_html=True)
            
            colA, colB = st.columns(2)
            with colA:
                st.markdown("### Average Scores")
                for pillar, vals in agg.items():
                    st.markdown(f"**{pillar.replace('_',' ').title()}:** {vals['avg']:.1f}/5  (min {vals['min']}–max {vals['max']})")
            
            with colB:
                st.markdown("### Radar (Average)")
                avg_scores = {k: v['avg'] for k,v in agg.items()}
                fig = create_radar_chart(avg_scores)
                st.plotly_chart(fig, use_container_width=True)
            
            disagreements = get_disagreement_areas()
            if disagreements:
                st.markdown("### ⚠️ Areas of Disagreement")
                for d in disagreements:
                    st.markdown(f"**{d['pillar']}:** spread {d['spread']:.1f} points (min {d['min']}–max {d['max']})")
            
            st.markdown("---")
            
            with st.expander("📋 Generate Action Playbook", expanded=not st.session_state.show_playbook):
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    playbook_company = st.text_input("Company name for Playbook")
                with col_p2:
                    playbook_location = st.text_input("Location for Playbook")
                if st.button("🚀 Generate Playbook"):
    try:
        # Проверим, что передаём
        st.write("Debug: agg =", agg)
        st.write("Debug: disagreements =", disagreements)
        
        playbook = generate_playbook(
            aggregated_scores=agg,
            disagreements=disagreements,
            company_name=playbook_company,
            location=playbook_location
        )
        st.session_state.generated_playbook = playbook
        st.session_state.show_playbook = True
        st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")
        )
        st.session_state.generated_playbook = playbook
        st.session_state.show_playbook = True
        st.rerun()
            
            if st.session_state.get('show_playbook') and st.session_state.get('generated_playbook'):
                with st.container():
                    st.markdown('<div class="playbook-section">', unsafe_allow_html=True)
                    st.markdown(format_playbook_for_display(st.session_state.generated_playbook))
                    playbook_md = export_playbook_to_markdown(st.session_state.generated_playbook)
                    b64 = base64.b64encode(playbook_md.encode()).decode()
                    href = f'<a href="data:text/markdown;base64,{b64}" download="AVCS_Playbook_{playbook_company or "audit"}.md"><button style="background-color:#1e3a8a; color:white; padding:8px 16px; margin-top:10px;">📥 Download Playbook (Markdown)</button></a>'
                    st.markdown(href, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                with st.expander("💾 Save this audit"):
                    company_name = st.text_input("Company name (optional)", key="save_company")
                    location = st.text_input("Location (optional)", key="save_location")
                    
                    if st.button("Save Audit to History"):
                        if company_name or location:
                            audit_id = save_audit(
                                practitioner_name=name,
                                company_name=company_name,
                                location=location,
                                total_score=total,
                                classification=cls_from_score(total),
                                scores_dict=avg_scores,
                                respondents_list=st.session_state.respondents
                            )
                            st.success(f"Audit saved! ID: {audit_id}")
                        else:
                            st.warning("Please enter at least company name or location")
            
            with col_s2:
                st.markdown("### Download PDF")
                pdf_data = create_pdf(avg_scores, total, 
                                     company_name if 'company_name' in locals() else "", 
                                     location if 'location' in locals() else "")
                href = f'<a href="data:application/octet-stream;base64,{pdf_data}" download="AVCS_Aggregated_Report.pdf"><button style="background-color:#1e3a8a; color:white; padding:8px 16px;">📥 Download PDF Report</button></a>'
                st.markdown(href, unsafe_allow_html=True)
            
            with col_s3:
                if st.button("➕ Add Another Respondent"):
                    st.session_state.step = 2
                    st.rerun()
            
            st.markdown("---")
            if st.button("← Back to Respondent List"):
                st.session_state.step = 1
                st.rerun()
