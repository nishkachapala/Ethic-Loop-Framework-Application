import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'ethic_loop.db')

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def calculate_risk_score(likelihood, impact):
    try:
        l = max(1, min(5, int(likelihood)))
        i = max(1, min(5, int(impact)))
        score = l * i
        if score <= 4:
            severity = 'Low'
        elif score <= 9:
            severity = 'Moderate'
        elif score <= 16:
            severity = 'High'
        else:
            severity = 'Critical'
        return score, severity
    except (ValueError, TypeError):
        return 1, 'Low'

DEFAULT_STAGES = [
    {
        'order': 1,
        'name': 'Requirements',
        'description': 'Identify societal values, legal compliance, and initial ethical impact assessments for system feasibility.',
        'ethical_requirements': 'Conduct initial Stakeholder Harm Analysis; draft Ethical Charter; define protected attributes and fair metrics; obtain multi-stakeholder feedback.',
        'checklists': [
            {"id": "req_1", "text": "Document primary and secondary stakeholder groups including vulnerable populations", "done": True},
            {"id": "req_2", "text": "Define legal, human rights, and institutional privacy obligations", "done": True},
            {"id": "req_3", "text": "Specify explicit non-goals to prevent ethical mission creep", "done": True},
            {"id": "req_4", "text": "Document formal justification for collecting each sensitive data field", "done": True}
        ]
    },
    {
        'order': 2,
        'name': 'Design',
        'description': 'Incorporate ethical architectural constraints, privacy-by-design, transparent UI, and explainability mechanisms.',
        'ethical_requirements': 'Embed privacy-by-design principles; establish algorithmic explainability wireframes; design human override workflows.',
        'checklists': [
            {"id": "des_1", "text": "Include clear user consent and opt-out pathways in UX blueprints", "done": True},
            {"id": "des_2", "text": "Design meaningful explainability indicators for automated recommendations", "done": True},
            {"id": "des_3", "text": "Architect fallback protocols and human-in-the-loop escalation paths", "done": True},
            {"id": "des_4", "text": "Evaluate adversarial threat model for ethical misuse vectors", "done": False}
        ]
    },
    {
        'order': 3,
        'name': 'Development',
        'description': 'Implement ethical algorithms, data hygiene pipelines, bias mitigation filters, and secure audit logging.',
        'ethical_requirements': 'Validate representative training dataset; implement differential privacy/pseudonymization; log algorithmic decision factors.',
        'checklists': [
            {"id": "dev_1", "text": "Apply data hygiene, deduplication, and demographic representation checks", "done": True},
            {"id": "dev_2", "text": "Enforce strict role-based access control (RBAC) on raw candidate datasets", "done": True},
            {"id": "dev_3", "text": "Implement immutable audit logs for automated decision traces", "done": True},
            {"id": "dev_4", "text": "Verify open-source libraries for licensing and ethical alignment", "done": False}
        ]
    },
    {
        'order': 4,
        'name': 'Testing',
        'description': 'Subject the system to fairness audits, stress testing, differential subgroup analysis, and accessibility checks.',
        'ethical_requirements': 'Execute demographic parity and equalized odds testing; test WCAG 2.1 AA accessibility; perform red-teaming.',
        'checklists': [
            {"id": "tst_1", "text": "Execute cross-demographic statistical parity tests across protected groups", "done": True},
            {"id": "tst_2", "text": "Conduct adversarial red-teaming to uncover hallucination and bias exploits", "done": False},
            {"id": "tst_3", "text": "Validate full screen-reader and WCAG 2.1 AA accessibility compliance", "done": False},
            {"id": "tst_4", "text": "Verify human override kill-switch triggers successfully under simulated failure", "done": True}
        ]
    },
    {
        'order': 5,
        'name': 'Deployment',
        'description': 'Stage controlled rollout with ethical pre-flight checklists, user notifications, and operational safeguards.',
        'ethical_requirements': 'Provide user transparency documentation; establish real-time drift detectors; prepare incident response playbook.',
        'checklists': [
            {"id": "dep_1", "text": "Publish accessible system card and model card documenting capabilities/limitations", "done": False},
            {"id": "dep_2", "text": "Train human operators on ethical escalation and override protocols", "done": False},
            {"id": "dep_3", "text": "Configure automated drift and disparate impact metric monitoring alerts", "done": False},
            {"id": "dep_4", "text": "Establish direct channels for affected users to appeal automated decisions", "done": False}
        ]
    },
    {
        'order': 6,
        'name': 'Maintenance',
        'description': 'Conduct ongoing ethical audits, monitor stakeholder feedback, manage post-deployment incidents, and retrain responsibly.',
        'ethical_requirements': 'Review periodic ethical audit reports; address user grievance filings; trigger stage reopening upon severe harm.',
        'checklists': [
            {"id": "mnt_1", "text": "Conduct quarterly algorithmic fairness and performance re-evaluations", "done": False},
            {"id": "mnt_2", "text": "Triage and resolve user ethical complaints within mandated SLA", "done": False},
            {"id": "mnt_3", "text": "Assess emergent risks from shifting real-world data distributions", "done": False},
            {"id": "mnt_4", "text": "Maintain transparent changelog of model retrainings and decision alterations", "done": False}
        ]
    }
]

DEFAULT_PILLARS = [
    {
        'code': 'E',
        'name': 'Ethical Impact Assessment',
        'purpose': 'Proactively identify and evaluate societal, psychological, environmental, and individual harms before and throughout development.',
        'questions': [
            {"q": "Has a formal stakeholder harm analysis been conducted including non-users?", "done": True},
            {"q": "Have privacy risks and data minimization principles been verified?", "done": True},
            {"q": "Are secondary and long-term societal externalities documented?", "done": True},
            {"q": "Is the system's purpose aligned with public interest and human dignity?", "done": True}
        ]
    },
    {
        'code': 'T',
        'name': 'Transparency and Trust',
        'purpose': 'Ensure algorithmic operations, data sources, decision criteria, and system constraints are understandable to stakeholders.',
        'questions': [
            {"q": "Are decisions accompanied by accessible and actionable explanations?", "done": False},
            {"q": "Is a Model/System Card detailing intended use and known limitations available?", "done": False},
            {"q": "Are end-users explicitly notified when interacting with an automated agent?", "done": True},
            {"q": "Are data retention and consent terms communicated in plain language?", "done": True}
        ]
    },
    {
        'code': 'H',
        'name': 'Human Oversight',
        'purpose': 'Guarantee meaningful human agency, actionable intervention mechanisms, and fallback safeguards for critical decisions.',
        'questions': [
            {"q": "Is there a designated human-in-the-loop reviewer with override authority?", "done": True},
            {"q": "Can automated decisions be halted immediately via a fail-safe kill-switch?", "done": True},
            {"q": "Are human operators properly trained on automation bias and complacency?", "done": False},
            {"q": "Is an appeals mechanism provided for impacted individuals?", "done": False}
        ]
    },
    {
        'code': 'I',
        'name': 'Inclusion and Fairness',
        'purpose': 'Eliminate unjust bias, preserve demographic fairness, and deliver equitable accessibility across diverse user cohorts.',
        'questions': [
            {"q": "Has training data been audited for demographic and historical imbalances?", "done": True},
            {"q": "Are disparate impact ratios monitored against protected attributes?", "done": True},
            {"q": "Does the user interface conform to WCAG 2.1 AA accessibility standards?", "done": False},
            {"q": "Were diverse community representatives consulted during requirements gathering?", "done": True}
        ]
    },
    {
        'code': 'C',
        'name': 'Continuous Accountability',
        'purpose': 'Maintain transparent governance, immutable audit logging, incident response loops, and regular third-party ethical reviews.',
        'questions': [
            {"q": "Are tamper-evident audit logs maintained for critical decision traces?", "done": True},
            {"q": "Is there an established post-deployment incident escalation policy?", "done": True},
            {"q": "Are regular independent ethical re-reviews scheduled in maintenance?", "done": False},
            {"q": "Can lifecycle stages be reopened when serious ethical flaws are reported?", "done": True}
        ]
    }
]

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript('''
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        domain TEXT NOT NULL,
        owner TEXT NOT NULL,
        created_at TEXT NOT NULL,
        current_stage TEXT NOT NULL DEFAULT 'Requirements',
        status TEXT NOT NULL DEFAULT 'Active',
        is_demo INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS lifecycle_stages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        stage_name TEXT NOT NULL,
        stage_order INTEGER NOT NULL,
        description TEXT,
        ethical_requirements TEXT,
        assigned_reviewer TEXT,
        status TEXT DEFAULT 'Pending',
        checklist_data TEXT,
        evidence_notes TEXT,
        completed_at TEXT,
        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS ethical_risks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        stage_name TEXT NOT NULL,
        pillar TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        affected_stakeholders TEXT,
        category TEXT NOT NULL,
        likelihood INTEGER NOT NULL,
        impact INTEGER NOT NULL,
        risk_score INTEGER NOT NULL,
        severity TEXT NOT NULL,
        mitigation_strategy TEXT,
        responsible_person TEXT,
        due_date TEXT,
        status TEXT NOT NULL DEFAULT 'Open',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS ethics_gates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        stage_name TEXT NOT NULL,
        reviewer_name TEXT NOT NULL,
        reviewer_role TEXT NOT NULL,
        risks_reviewed TEXT,
        evidence_reviewed TEXT,
        review_notes TEXT NOT NULL,
        decision TEXT NOT NULL,
        conditions TEXT,
        required_actions TEXT,
        action_owner TEXT,
        target_completion_date TEXT,
        review_date TEXT NOT NULL,
        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS pillar_assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        pillar_code TEXT NOT NULL,
        pillar_name TEXT NOT NULL,
        purpose TEXT,
        checklist_data TEXT,
        evidence_notes TEXT,
        status TEXT DEFAULT 'Pending',
        completed_at TEXT,
        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        incident_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        pillar_impacted TEXT NOT NULL,
        reported_by TEXT NOT NULL,
        date_reported TEXT NOT NULL,
        remediation_notes TEXT,
        status TEXT DEFAULT 'Open',
        reopened_stage TEXT,
        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS corrective_actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        gate_id INTEGER,
        risk_id INTEGER,
        action_title TEXT NOT NULL,
        description TEXT NOT NULL,
        assigned_to TEXT NOT NULL,
        due_date TEXT,
        status TEXT DEFAULT 'Open',
        resolution_notes TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY(gate_id) REFERENCES ethics_gates(id) ON DELETE SET NULL,
        FOREIGN KEY(risk_id) REFERENCES ethical_risks(id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        action_type TEXT NOT NULL,
        description TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
    );
    ''')

    conn.commit()

    # Check if we should seed default demonstration data
    cursor.execute("SELECT COUNT(*) FROM projects")
    count = cursor.fetchone()[0]
    if count == 0:
        seed_database(conn)
    conn.close()

def log_activity(conn, project_id, action_type, description):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute(
        "INSERT INTO activity_logs (project_id, action_type, description, timestamp) VALUES (?, ?, ?, ?)",
        (project_id, action_type, description, now)
    )

def seed_database(conn):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Demo Project 1: AI Recruitment System
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO projects (name, description, domain, owner, created_at, current_stage, status, is_demo)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
    ''', (
        'AI Recruitment & Resume Screening System',
        'Automated applicant ranking and resume parsing pipeline deployed for talent acquisition. Uses NLP embeddings and historical hiring dataset.',
        'Human Resources / Machine Learning',
        'TalentTech Solutions (Demo)',
        now,
        'Testing',
        'Remediating'
    ))
    p1_id = cur.lastrowid
    log_activity(conn, p1_id, 'PROJECT_CREATED', 'Project "AI Recruitment & Resume Screening System" initialized (Demo data).')

    # Seed Stages for Project 1
    stages_p1 = [
        ('Requirements', 1, 'Passed Gate', 'Elena Vance (Lead Ethicist)', 'Completed stakeholder impact matrix and bias risk threshold definitions.'),
        ('Design', 2, 'Passed Gate', 'Marcus Brody (System Architect)', 'Incorporated candidate transparency portal and manual review trigger specs.'),
        ('Development', 3, 'Passed Gate', 'Dev Team Lead', 'Implemented candidate redaction module; logged embeddings in audit database.'),
        ('Testing', 4, 'Remediating', 'Dr. Sarah Lin (Ethics Auditor)', 'Algorithmic fairness testing revealed severe disparate impact ratio (0.72) for gender attributes.'),
        ('Deployment', 5, 'Pending', 'DevOps Ops Lead', 'Gated pending resolution of demographic disparity remediation.'),
        ('Maintenance', 6, 'Pending', 'Support & Governance Lead', 'Scheduled quarterly continuous accountability audits post-release.')
    ]
    for s_name, s_order, s_status, s_rev, s_notes in stages_p1:
        s_template = next(s for s in DEFAULT_STAGES if s['name'] == s_name)
        cur.execute('''
            INSERT INTO lifecycle_stages (project_id, stage_name, stage_order, description, ethical_requirements, assigned_reviewer, status, checklist_data, evidence_notes, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            p1_id, s_name, s_order, s_template['description'], s_template['ethical_requirements'],
            s_rev, s_status, json.dumps(s_template['checklists']), s_notes,
            now if s_status == 'Passed Gate' else None
        ))

    # Seed Pillars for Project 1
    for p in DEFAULT_PILLARS:
        p_status = 'Completed' if p['code'] in ['E', 'C'] else 'In Progress'
        cur.execute('''
            INSERT INTO pillar_assessments (project_id, pillar_code, pillar_name, purpose, checklist_data, evidence_notes, status, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            p1_id, p['code'], p['name'], p['purpose'],
            json.dumps(p['questions']),
            f"Evidence compiled for {p['name']}. Review performed against ethical SDLC guidelines.",
            p_status,
            now if p_status == 'Completed' else None
        ))

    # Seed 5 specific risks from Scenario for AI Recruitment
    risks_data = [
        (
            'Unfair candidate screening against protected demographics',
            'Historical training resume dataset over-indexes on male candidate profiles from top-tier private universities, penalizing qualified female applicants and non-traditional backgrounds.',
            'Job applicants, minority cohorts, HR compliance officers',
            'Inclusion and Fairness',
            'Testing',
            'Bias and discrimination',
            4, 5,
            'Retrain embeddings with synthetic balancing; perform demographic parity re-weighting; enforce minimum 80% four-fifths rule threshold.',
            'Dr. Sarah Lin (Lead Auditor)',
            '2026-11-15',
            'Under Review'
        ),
        (
            'Unauthorized access or leakage of confidential candidate data',
            'Resume PDFs contain personal identifying data, contact details, disability status disclosures, and previous salary records.',
            'Applicants, Data Protection Officer',
            'Ethical Impact Assessment',
            'Development',
            'Privacy',
            3, 4,
            'Implement column-level AES-256 encryption and automatic PII redaction pipeline before ML vectorization.',
            'Marcus Brody (Security Lead)',
            '2026-11-05',
            'Mitigating'
        ),
        (
            'Lack of actionable explanation for automated rejection decisions',
            'Deep neural net ranking provides opaque composite numerical scores without interpretable feature attribution, frustrating candidates and hindering appeal.',
            'Rejected candidates, Career counselors',
            'Transparency and Trust',
            'Design',
            'Transparency',
            4, 3,
            'Integrate SHAP/LIME feature attribution explanations rendered in plain language candidate feedback summaries.',
            'Maya Thorne (UX Designer)',
            '2026-11-20',
            'Open'
        ),
        (
            'Insufficient human review on auto-rejected borderline applicants',
            'Recruiters accept automated filtering recommendations without spot-checking borderline candidates, inducing automation complacency.',
            'Recruiters, Hiring Managers, Borderline candidates',
            'Human Oversight',
            'Testing',
            'Human oversight',
            3, 4,
            'Enforce mandatory double-blind human inspection for any score within 15% of the acceptance threshold.',
            'Elena Vance (Ethics Chair)',
            '2026-11-12',
            'Mitigating'
        ),
        (
            'Accessibility barriers in applicant evaluation interface',
            'Visual candidate assessment portal lacks ARIA landmarks, keyboard-only tab navigation, and sufficient color contrast ratios.',
            'Applicants with visual or motor disabilities',
            'Inclusion and Fairness',
            'Design',
            'Accessibility',
            3, 3,
            'Audit against WCAG 2.1 AA standards; add automated axe-core accessibility unit tests to CI/CD pipeline.',
            'Frontend Engineering Team',
            '2026-11-08',
            'Open'
        )
    ]

    for title, desc, stkh, pillar, stg, cat, lik, imp, mit, resp, due, r_stat in risks_data:
        score, sev = calculate_risk_score(lik, imp)
        cur.execute('''
            INSERT INTO ethical_risks (
                project_id, stage_name, pillar, title, description, affected_stakeholders,
                category, likelihood, impact, risk_score, severity, mitigation_strategy,
                responsible_person, due_date, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            p1_id, stg, pillar, title, desc, stkh, cat, lik, imp, score, sev, mit, resp, due, r_stat, now, now
        ))

    # Seed Gate Review for Project 1 (Testing Stage - Remediate)
    cur.execute('''
        INSERT INTO ethics_gates (
            project_id, stage_name, reviewer_name, reviewer_role, risks_reviewed,
            evidence_reviewed, review_notes, decision, conditions, required_actions,
            action_owner, target_completion_date, review_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        p1_id, 'Testing', 'Dr. Sarah Lin', 'Lead Ethical Compliance Officer',
        'Bias & discrimination risk (Score 20 - Critical); Human oversight risk (Score 12 - High)',
        'Disparate impact ratio audit run #104 showed female candidate selection rate of 0.61 against baseline male cohort (statistically significant disparity).',
        'Project cannot proceed to Deployment until disparate impact is corrected. Low algorithmic error rate does not supersede fundamental non-discrimination obligations.',
        'Remediate and Review Again',
        None,
        'Investigate historical training data for demographic skew. Implement fairness constraints/re-weighting. Retest pass rates across all cohorts and resubmit with audit certificate.',
        'ML Training Team (Lead: Kevin Chen)',
        '2026-11-18',
        '2026-10-25 14:30:00'
    ))
    gate_id = cur.lastrowid

    # Seed Corrective Action linked to Gate
    cur.execute('''
        INSERT INTO corrective_actions (
            project_id, gate_id, risk_id, action_title, description, assigned_to, due_date, status, resolution_notes, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        p1_id, gate_id, 1,
        'Demographic parity retraining & disparate impact audit',
        'Audit 2018-2024 training resumes, strip non-predictive gender signals, apply Fairlearn parity optimizer, and generate verifiable audit delta.',
        'Kevin Chen (ML Engineer)',
        '2026-11-18',
        'In Progress',
        'Preliminary rescoring shows disparate impact improved to 0.88 in local benchmark. Comprehensive re-audit validation pending.',
        now
    ))

    # Seed Demonstration Incident for Project 1
    cur.execute('''
        INSERT INTO incidents (
            project_id, title, description, incident_type, severity, pillar_impacted,
            reported_by, date_reported, remediation_notes, status, reopened_stage
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        p1_id,
        'Candidate formal grievance on non-traditional degree penalty',
        'Applicant with 10 years open-source experience was automatically rejected due to missing accredited university keyword, highlighting heuristic over-rigidity.',
        'User Complaint',
        'Moderate',
        'Inclusion and Fairness',
        'Public Ombudsperson Portal',
        '2026-10-26 09:15:00',
        'Manual candidate application restored for human interview. Adjusting resume parser to value practical open-source portfolio repositories.',
        'Investigating',
        None
    ))

    # Demo Project 2: Healthcare Diagnostic Assistant
    cur.execute('''
        INSERT INTO projects (name, description, domain, owner, created_at, current_stage, status, is_demo)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
    ''', (
        'CardioVision: Clinical Decision Support AI',
        'Predictive ECG pattern recognition assistant assisting cardiologists with early arrhythmia and ischemic risk triage in emergency departments.',
        'Healthcare / Medical Diagnostics',
        'HealthCare AI Research Lab (Demo)',
        now,
        'Design',
        'Active'
    ))
    p2_id = cur.lastrowid
    log_activity(conn, p2_id, 'PROJECT_CREATED', 'Project "CardioVision" initialized (Demo data).')

    for s_name, s_order, s_status, s_rev, s_notes in [
        ('Requirements', 1, 'Passed Gate', 'Clinical Ethics Board', 'Approved ethical clinical trial protocols and patient data privacy covenants.'),
        ('Design', 2, 'In Progress', 'Dr. Aris Thorne (Chief Medical Officer)', 'Designing clinician override telemetry and false-negative alert safeguards.'),
        ('Development', 3, 'Pending', 'Bioinformatics Lead', 'Awaiting signed design specifications.'),
        ('Testing', 4, 'Pending', 'Clinical Validation Unit', 'Pending development milestones.'),
        ('Deployment', 5, 'Pending', 'Hospital IT Ops', 'Pending clinical trial validation.'),
        ('Maintenance', 6, 'Pending', 'Patient Safety Committee', 'Pending clinical deployment.')
    ]:
        s_template = next(s for s in DEFAULT_STAGES if s['name'] == s_name)
        cur.execute('''
            INSERT INTO lifecycle_stages (project_id, stage_name, stage_order, description, ethical_requirements, assigned_reviewer, status, checklist_data, evidence_notes, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            p2_id, s_name, s_order, s_template['description'], s_template['ethical_requirements'],
            s_rev, s_status, json.dumps(s_template['checklists']), s_notes,
            now if s_status == 'Passed Gate' else None
        ))

    for p in DEFAULT_PILLARS:
        cur.execute('''
            INSERT INTO pillar_assessments (project_id, pillar_code, pillar_name, purpose, checklist_data, evidence_notes, status, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            p2_id, p['code'], p['name'], p['purpose'],
            json.dumps(p['questions']),
            f"Preliminary clinical governance review for {p['name']}.",
            'In Progress', None
        ))

    # Seed Risk for Project 2
    cur.execute('''
        INSERT INTO ethical_risks (
            project_id, stage_name, pillar, title, description, affected_stakeholders,
            category, likelihood, impact, risk_score, severity, mitigation_strategy,
            responsible_person, due_date, status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        p2_id, 'Design', 'Human Oversight',
        'Automation complacency leading to missed atypical ECG presentations',
        'Junior clinicians may over-rely on AI negative predictions, failing to conduct manual tactile inspections on complex atypical cardiac cases.',
        'Emergency patients, attending physicians, hospital risk managers',
        'Human oversight',
        3, 5, 15, 'High',
        'Design affirmative confirmation dialogues requiring clinicians to examine raw rhythm strips before dismissing alerts; periodic unannounced calibration drills.',
        'Dr. Aris Thorne', '2026-11-30', 'Mitigating', now, now
    ))

    # Demo Project 3: Adaptive Student Assessment AI
    cur.execute('''
        INSERT INTO projects (name, description, domain, owner, created_at, current_stage, status, is_demo)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
    ''', (
        'EduAssess: Adaptive Academic Proctoring & Evaluation',
        'Automated proctoring platform monitoring webcams and keystroke cadence during high-stakes university examinations.',
        'Education / Automated Proctoring',
        'EdTech Innovations Group (Demo)',
        now,
        'Requirements',
        'In Gate Review'
    ))
    p3_id = cur.lastrowid
    log_activity(conn, p3_id, 'PROJECT_CREATED', 'Project "EduAssess" initialized (Demo data).')

    for s_name, s_order, s_status, s_rev, s_notes in [
        ('Requirements', 1, 'Gate Review Pending', 'University Academic Senate', 'Ethics review ongoing regarding invasive biometric webcam surveillance and neurodivergent student accommodations.'),
        ('Design', 2, 'Pending', 'Pedagogy Tech Team', 'Pending requirements approval.'),
        ('Development', 3, 'Pending', 'Software Dev Team', 'Pending specifications.'),
        ('Testing', 4, 'Pending', 'Student Welfare Audit', 'Pending development.'),
        ('Deployment', 5, 'Pending', 'Campus IT Ops', 'Pending testing.'),
        ('Maintenance', 6, 'Pending', 'Student Grievance Office', 'Pending deployment.')
    ]:
        s_template = next(s for s in DEFAULT_STAGES if s['name'] == s_name)
        cur.execute('''
            INSERT INTO lifecycle_stages (project_id, stage_name, stage_order, description, ethical_requirements, assigned_reviewer, status, checklist_data, evidence_notes, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            p3_id, s_name, s_order, s_template['description'], s_template['ethical_requirements'],
            s_rev, s_status, json.dumps(s_template['checklists']), s_notes, None
        ))

    for p in DEFAULT_PILLARS:
        cur.execute('''
            INSERT INTO pillar_assessments (project_id, pillar_code, pillar_name, purpose, checklist_data, evidence_notes, status, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            p3_id, p['code'], p['name'], p['purpose'],
            json.dumps(p['questions']),
            f"Undergraduate privacy impact assessment for {p['name']}.",
            'Pending', None
        ))

    # Seed Risk for Project 3
    cur.execute('''
        INSERT INTO ethical_risks (
            project_id, stage_name, pillar, title, description, affected_stakeholders,
            category, likelihood, impact, risk_score, severity, mitigation_strategy,
            responsible_person, due_date, status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        p3_id, 'Requirements', 'Inclusion and Fairness',
        'Disproportionate flagging of neurodivergent students and varying lighting environments',
        'Gaze-tracking algorithms flag natural eye movements of autistic students and darker skin tones under dim dorm lighting as suspicious cheating behavior.',
        'Students with ADHD/Autism, lower-income students, faculty adjudicators',
        'Bias and discrimination',
        5, 4, 20, 'Critical',
        'Ban automatic punitive actions; require faculty manual video review with disability accommodation context before any infraction flag is posted.',
        'Prof. Miriam Kroll', '2026-11-10', 'Open', now, now
    ))

    conn.commit()
