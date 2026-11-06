import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, Response, make_response
import io

from models import (
    init_db, get_db, calculate_risk_score, log_activity,
    DEFAULT_STAGES, DEFAULT_PILLARS
)
import report_generator

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ethic-loop-secret-key-academic-2026')

# Initialize DB on start
with app.app_context():
    init_db()

@app.context_processor
def inject_global_data():
    conn = get_db()
    projects = conn.execute("SELECT id, name, is_demo FROM projects ORDER BY name ASC").fetchall()
    conn.close()
    return {
        'nav_projects': projects,
        'current_year': datetime.now().year,
        'framework_name': 'ETHIC-Loop',
        'framework_notice': 'ETHIC-Loop is a proposed conceptual framework for academic research and pedagogy, not an established international standard or an empirically validated methodology.'
    }

# ----------------- DASHBOARD -----------------
@app.route('/')
def dashboard():
    conn = get_db()

    # Total projects
    total_projects = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]

    # Total risks
    total_risks = conn.execute("SELECT COUNT(*) FROM ethical_risks").fetchone()[0]

    # Open high-priority risks (High or Critical)
    open_high_risks = conn.execute(
        "SELECT COUNT(*) FROM ethical_risks WHERE severity IN ('High', 'Critical') AND status != 'Resolved'"
    ).fetchone()[0]

    # Gate decisions summary
    gate_counts_raw = conn.execute(
        "SELECT decision, COUNT(*) as cnt FROM ethics_gates GROUP BY decision"
    ).fetchall()
    gate_decisions = {
        'Proceed': 0,
        'Proceed with Conditions': 0,
        'Remediate': 0,
        'Stop or Escalate': 0
    }
    for row in gate_counts_raw:
        d = row['decision']
        if 'Proceed with Conditions' in d:
            gate_decisions['Proceed with Conditions'] += row['cnt']
        elif 'Proceed' in d:
            gate_decisions['Proceed'] += row['cnt']
        elif 'Remediate' in d:
            gate_decisions['Remediate'] += row['cnt']
        elif 'Stop' in d or 'Escalate' in d:
            gate_decisions['Stop or Escalate'] += row['cnt']

    # Projects by SDLC stage
    stages_order = ['Requirements', 'Design', 'Development', 'Testing', 'Deployment', 'Maintenance']
    projects_by_stage_raw = conn.execute(
        "SELECT current_stage, COUNT(*) as cnt FROM projects GROUP BY current_stage"
    ).fetchall()
    stage_map = {s: 0 for s in stages_order}
    for row in projects_by_stage_raw:
        if row['current_stage'] in stage_map:
            stage_map[row['current_stage']] = row['cnt']

    # Risk severity distribution
    severity_order = ['Low', 'Moderate', 'High', 'Critical']
    risk_sev_raw = conn.execute(
        "SELECT severity, COUNT(*) as cnt FROM ethical_risks GROUP BY severity"
    ).fetchall()
    sev_map = {s: 0 for s in severity_order}
    for row in risk_sev_raw:
        if row['severity'] in sev_map:
            sev_map[row['severity']] = row['cnt']

    # Recent activities
    recent_activities = conn.execute(
        """SELECT a.*, p.name as project_name
           FROM activity_logs a
           LEFT JOIN projects p ON a.project_id = p.id
           ORDER BY a.id DESC LIMIT 8"""
    ).fetchall()

    # Overall ethical review progress
    total_stages = conn.execute("SELECT COUNT(*) FROM lifecycle_stages").fetchone()[0]
    passed_stages = conn.execute("SELECT COUNT(*) FROM lifecycle_stages WHERE status = 'Passed Gate'").fetchone()[0]
    review_progress = int((passed_stages / total_stages * 100)) if total_stages > 0 else 0

    # Recent projects
    recent_projects = conn.execute(
        "SELECT * FROM projects ORDER BY id DESC LIMIT 5"
    ).fetchall()

    conn.close()

    return render_template(
        'dashboard.html',
        total_projects=total_projects,
        total_risks=total_risks,
        open_high_risks=open_high_risks,
        gate_decisions=gate_decisions,
        stage_labels=stages_order,
        stage_counts=[stage_map[s] for s in stages_order],
        sev_labels=severity_order,
        sev_counts=[sev_map[s] for s in severity_order],
        recent_activities=recent_activities,
        review_progress=review_progress,
        recent_projects=recent_projects
    )

# ----------------- PROJECTS -----------------
@app.route('/projects')
def projects_list():
    conn = get_db()
    query = "SELECT p.*, (SELECT COUNT(*) FROM ethical_risks r WHERE r.project_id = p.id) as risk_count, (SELECT COUNT(*) FROM incidents i WHERE i.project_id = p.id) as incident_count FROM projects p WHERE 1=1"
    params = []

    domain_filter = request.args.get('domain', '').strip()
    stage_filter = request.args.get('stage', '').strip()
    status_filter = request.args.get('status', '').strip()
    search = request.args.get('q', '').strip()

    if domain_filter:
        query += " AND p.domain LIKE ?"
        params.append(f"%{domain_filter}%")
    if stage_filter:
        query += " AND p.current_stage = ?"
        params.append(stage_filter)
    if status_filter:
        query += " AND p.status = ?"
        params.append(status_filter)
    if search:
        query += " AND (p.name LIKE ? OR p.description LIKE ? OR p.owner LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    query += " ORDER BY p.id ASC"
    projects = conn.execute(query, params).fetchall()

    domains = conn.execute("SELECT DISTINCT domain FROM projects ORDER BY domain").fetchall()
    conn.close()

    return render_template('projects.html', projects=projects, domains=domains,
                           domain_filter=domain_filter, stage_filter=stage_filter,
                           status_filter=status_filter, search=search)

@app.route('/projects/create', methods=['POST'])
def create_project():
    name = request.form.get('name', '').strip()
    domain = request.form.get('domain', '').strip()
    owner = request.form.get('owner', '').strip()
    description = request.form.get('description', '').strip()
    current_stage = request.form.get('current_stage', 'Requirements').strip()

    if not name or not domain or not owner:
        flash('Project name, domain, and team/owner are required fields.', 'danger')
        return redirect(url_for('projects_list'))

    conn = get_db()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO projects (name, description, domain, owner, created_at, current_stage, status, is_demo)
        VALUES (?, ?, ?, ?, ?, ?, 'Active', 0)
    ''', (name, description, domain, owner, now, current_stage))
    project_id = cur.lastrowid

    # Populate 6 default stages
    for s in DEFAULT_STAGES:
        st_status = 'In Progress' if s['name'] == current_stage else 'Pending'
        cur.execute('''
            INSERT INTO lifecycle_stages (project_id, stage_name, stage_order, description, ethical_requirements, assigned_reviewer, status, checklist_data, evidence_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            project_id, s['name'], s['order'], s['description'], s['ethical_requirements'],
            owner, st_status, json.dumps(s['checklists']), 'Initial setup stage checklist.'
        ))

    # Populate 5 default pillars
    for p in DEFAULT_PILLARS:
        cur.execute('''
            INSERT INTO pillar_assessments (project_id, pillar_code, pillar_name, purpose, checklist_data, evidence_notes, status)
            VALUES (?, ?, ?, ?, ?, ?, 'Pending')
        ''', (
            project_id, p['code'], p['name'], p['purpose'], json.dumps(p['questions']),
            f"Preliminary scoping for {p['name']}."
        ))

    log_activity(conn, project_id, 'PROJECT_CREATED', f"Project '{name}' created by {owner}.")
    conn.commit()
    conn.close()

    flash(f"Project '{name}' successfully created with 6 SDLC stages and 5 Ethical Pillars initialized.", 'success')
    return redirect(url_for('project_detail', project_id=project_id))

@app.route('/projects/<int:project_id>')
def project_detail(project_id):
    conn = get_db()
    project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not project:
        conn.close()
        flash('Project not found.', 'danger')
        return redirect(url_for('projects_list'))

    stages = conn.execute("SELECT * FROM lifecycle_stages WHERE project_id = ? ORDER BY stage_order ASC", (project_id,)).fetchall()
    risks = conn.execute("SELECT * FROM ethical_risks WHERE project_id = ? ORDER BY risk_score DESC", (project_id,)).fetchall()
    gates = conn.execute("SELECT * FROM ethics_gates WHERE project_id = ? ORDER BY id DESC", (project_id,)).fetchall()
    pillars = conn.execute("SELECT * FROM pillar_assessments WHERE project_id = ? ORDER BY id ASC", (project_id,)).fetchall()
    incidents = conn.execute("SELECT * FROM incidents WHERE project_id = ? ORDER BY id DESC", (project_id,)).fetchall()
    actions = conn.execute("SELECT * FROM corrective_actions WHERE project_id = ? ORDER BY id DESC", (project_id,)).fetchall()
    activities = conn.execute("SELECT * FROM activity_logs WHERE project_id = ? ORDER BY id DESC LIMIT 10", (project_id,)).fetchall()

    conn.close()
    return render_template(
        'project_detail.html',
        project=project,
        stages=stages,
        risks=risks,
        gates=gates,
        pillars=pillars,
        incidents=incidents,
        actions=actions,
        activities=activities
    )

@app.route('/projects/<int:project_id>/edit', methods=['POST'])
def edit_project(project_id):
    name = request.form.get('name', '').strip()
    domain = request.form.get('domain', '').strip()
    owner = request.form.get('owner', '').strip()
    description = request.form.get('description', '').strip()
    current_stage = request.form.get('current_stage', '').strip()
    status = request.form.get('status', '').strip()

    if not name or not domain or not owner:
        flash('Name, domain, and owner are required.', 'danger')
        return redirect(url_for('project_detail', project_id=project_id))

    conn = get_db()
    conn.execute('''
        UPDATE projects
        SET name = ?, domain = ?, owner = ?, description = ?, current_stage = ?, status = ?
        WHERE id = ?
    ''', (name, domain, owner, description, current_stage, status, project_id))

    log_activity(conn, project_id, 'PROJECT_UPDATED', f"Project details updated for '{name}'.")
    conn.commit()
    conn.close()

    flash('Project updated successfully.', 'success')
    return redirect(url_for('project_detail', project_id=project_id))

@app.route('/projects/<int:project_id>/delete', methods=['POST'])
def delete_project(project_id):
    conn = get_db()
    project = conn.execute("SELECT name FROM projects WHERE id = ?", (project_id,)).fetchone()
    if project:
        proj_name = project['name']
        conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        log_activity(conn, None, 'PROJECT_DELETED', f"Project '{proj_name}' (ID: {project_id}) was deleted.")
        conn.commit()
        flash(f"Project '{proj_name}' and all associated records deleted.", 'success')
    conn.close()
    return redirect(url_for('projects_list'))

# ----------------- SDLC WORKFLOW -----------------
@app.route('/workflow')
def workflow():
    conn = get_db()
    projects = conn.execute("SELECT * FROM projects ORDER BY id ASC").fetchall()
    if not projects:
        conn.close()
        flash('Please create a project first.', 'info')
        return redirect(url_for('projects_list'))

    project_id = request.args.get('project_id', type=int)
    if not project_id:
        project_id = projects[0]['id']

    current_project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    stages = conn.execute("SELECT * FROM lifecycle_stages WHERE project_id = ? ORDER BY stage_order ASC", (project_id,)).fetchall()
    risks = conn.execute("SELECT * FROM ethical_risks WHERE project_id = ?", (project_id,)).fetchall()
    gates = conn.execute("SELECT * FROM ethics_gates WHERE project_id = ? ORDER BY id DESC", (project_id,)).fetchall()

    # Parse JSON checklists for frontend rendering
    stages_data = []
    for s in stages:
        s_dict = dict(s)
        try:
            s_dict['checklists'] = json.loads(s['checklist_data'] or '[]')
        except:
            s_dict['checklists'] = []
        stages_data.append(s_dict)

    conn.close()
    return render_template('workflow.html', projects=projects, project=current_project,
                           stages=stages_data, risks=risks, gates=gates)

@app.route('/api/stages/<int:stage_id>/save', methods=['POST'])
def save_stage(stage_id):
    conn = get_db()
    stage = conn.execute("SELECT * FROM lifecycle_stages WHERE id = ?", (stage_id,)).fetchone()
    if not stage:
        conn.close()
        return jsonify({'success': False, 'error': 'Stage not found'}), 404

    status = request.form.get('status', stage['status'])
    assigned_reviewer = request.form.get('assigned_reviewer', stage['assigned_reviewer'])
    evidence_notes = request.form.get('evidence_notes', stage['evidence_notes'])

    # Checklist update from form
    try:
        current_checklists = json.loads(stage['checklist_data'] or '[]')
    except:
        current_checklists = []

    for item in current_checklists:
        c_id = item.get('id')
        item['done'] = (request.form.get(f'chk_{c_id}') == 'on')

    completed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if status == 'Passed Gate' else stage['completed_at']

    conn.execute('''
        UPDATE lifecycle_stages
        SET status = ?, assigned_reviewer = ?, evidence_notes = ?, checklist_data = ?, completed_at = ?
        WHERE id = ?
    ''', (status, assigned_reviewer, evidence_notes, json.dumps(current_checklists), completed_at, stage_id))

    log_activity(conn, stage['project_id'], 'STAGE_UPDATED', f"Stage '{stage['stage_name']}' updated to status '{status}'.")
    conn.commit()
    conn.close()

    flash(f"Stage '{stage['stage_name']}' saved successfully.", 'success')
    return redirect(url_for('workflow', project_id=stage['project_id']))

# ----------------- ETHICAL RISKS ASSESSMENT -----------------
@app.route('/risks')
def risks():
    conn = get_db()
    projects = conn.execute("SELECT * FROM projects ORDER BY id ASC").fetchall()
    project_id = request.args.get('project_id', type=int)

    query = "SELECT r.*, p.name as project_name FROM ethical_risks r JOIN projects p ON r.project_id = p.id WHERE 1=1"
    params = []

    if project_id:
        query += " AND r.project_id = ?"
        params.append(project_id)

    pillar_filter = request.args.get('pillar', '').strip()
    stage_filter = request.args.get('stage', '').strip()
    sev_filter = request.args.get('severity', '').strip()
    status_filter = request.args.get('status', '').strip()
    category_filter = request.args.get('category', '').strip()
    search = request.args.get('q', '').strip()

    if pillar_filter:
        query += " AND r.pillar LIKE ?"
        params.append(f"%{pillar_filter}%")
    if stage_filter:
        query += " AND r.stage_name = ?"
        params.append(stage_filter)
    if sev_filter:
        query += " AND r.severity = ?"
        params.append(sev_filter)
    if status_filter:
        query += " AND r.status = ?"
        params.append(status_filter)
    if category_filter:
        query += " AND r.category = ?"
        params.append(category_filter)
    if search:
        query += " AND (r.title LIKE ? OR r.description LIKE ? OR r.mitigation_strategy LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    query += " ORDER BY r.risk_score DESC, r.id DESC"
    risks_list = [dict(r) for r in conn.execute(query, params).fetchall()]

    # Calculate 5x5 Matrix counts for the selected project (or all)
    matrix_query = "SELECT likelihood, impact, COUNT(*) as cnt FROM ethical_risks WHERE 1=1"
    m_params = []
    if project_id:
        matrix_query += " AND project_id = ?"
        m_params.append(project_id)
    matrix_query += " GROUP BY likelihood, impact"

    matrix_rows = conn.execute(matrix_query, m_params).fetchall()
    matrix = {}
    for l in range(1, 6):
        for i in range(1, 6):
            matrix[(l, i)] = 0
    for row in matrix_rows:
        matrix[(row['likelihood'], row['impact'])] = row['cnt']

    selected_project = None
    if project_id:
        selected_project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()

    conn.close()

    return render_template(
        'risks.html',
        projects=projects,
        selected_project=selected_project,
        project_id=project_id,
        risks=risks_list,
        matrix=matrix,
        pillar_filter=pillar_filter,
        stage_filter=stage_filter,
        sev_filter=sev_filter,
        status_filter=status_filter,
        category_filter=category_filter,
        search=search
    )

@app.route('/api/risks/create', methods=['POST'])
def create_risk():
    project_id = request.form.get('project_id', type=int)
    stage_name = request.form.get('stage_name', 'Requirements').strip()
    pillar = request.form.get('pillar', 'Ethical Impact Assessment').strip()
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    affected_stakeholders = request.form.get('affected_stakeholders', '').strip()
    category = request.form.get('category', 'Bias and discrimination').strip()
    likelihood = int(request.form.get('likelihood', 3))
    impact = int(request.form.get('impact', 3))
    mitigation_strategy = request.form.get('mitigation_strategy', '').strip()
    responsible_person = request.form.get('responsible_person', '').strip()
    due_date = request.form.get('due_date', '').strip()
    status = request.form.get('status', 'Open').strip()

    if not project_id or not title:
        flash('Project and Risk Title are mandatory.', 'danger')
        return redirect(url_for('risks', project_id=project_id))

    score, severity = calculate_risk_score(likelihood, impact)
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db()
    conn.execute('''
        INSERT INTO ethical_risks (
            project_id, stage_name, pillar, title, description, affected_stakeholders,
            category, likelihood, impact, risk_score, severity, mitigation_strategy,
            responsible_person, due_date, status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        project_id, stage_name, pillar, title, description, affected_stakeholders,
        category, likelihood, impact, score, severity, mitigation_strategy,
        responsible_person, due_date, status, now, now
    ))

    log_activity(conn, project_id, 'RISK_LOGGED', f"New ethical risk logged: '{title}' (Score: {score} - {severity}).")
    conn.commit()
    conn.close()

    flash(f"Ethical risk '{title}' logged successfully (Score: {score} [{severity}]).", 'success')
    return redirect(url_for('risks', project_id=project_id))

@app.route('/api/risks/<int:risk_id>/edit', methods=['POST'])
def edit_risk(risk_id):
    conn = get_db()
    risk = conn.execute("SELECT * FROM ethical_risks WHERE id = ?", (risk_id,)).fetchone()
    if not risk:
        conn.close()
        flash('Risk record not found.', 'danger')
        return redirect(url_for('risks'))

    title = request.form.get('title', risk['title']).strip()
    stage_name = request.form.get('stage_name', risk['stage_name']).strip()
    pillar = request.form.get('pillar', risk['pillar']).strip()
    description = request.form.get('description', risk['description']).strip()
    affected_stakeholders = request.form.get('affected_stakeholders', risk['affected_stakeholders']).strip()
    category = request.form.get('category', risk['category']).strip()
    likelihood = int(request.form.get('likelihood', risk['likelihood']))
    impact = int(request.form.get('impact', risk['impact']))
    mitigation_strategy = request.form.get('mitigation_strategy', risk['mitigation_strategy']).strip()
    responsible_person = request.form.get('responsible_person', risk['responsible_person']).strip()
    due_date = request.form.get('due_date', risk['due_date']).strip()
    status = request.form.get('status', risk['status']).strip()

    score, severity = calculate_risk_score(likelihood, impact)
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn.execute('''
        UPDATE ethical_risks
        SET title = ?, stage_name = ?, pillar = ?, description = ?, affected_stakeholders = ?,
            category = ?, likelihood = ?, impact = ?, risk_score = ?, severity = ?,
            mitigation_strategy = ?, responsible_person = ?, due_date = ?, status = ?, updated_at = ?
        WHERE id = ?
    ''', (
        title, stage_name, pillar, description, affected_stakeholders,
        category, likelihood, impact, score, severity,
        mitigation_strategy, responsible_person, due_date, status, now, risk_id
    ))

    log_activity(conn, risk['project_id'], 'RISK_UPDATED', f"Risk '{title}' updated (Score: {score} - {severity}, Status: {status}).")
    conn.commit()
    conn.close()

    flash(f"Risk '{title}' updated successfully.", 'success')
    return redirect(url_for('risks', project_id=risk['project_id']))

@app.route('/api/risks/<int:risk_id>/delete', methods=['POST'])
def delete_risk(risk_id):
    conn = get_db()
    risk = conn.execute("SELECT * FROM ethical_risks WHERE id = ?", (risk_id,)).fetchone()
    if risk:
        p_id = risk['project_id']
        r_title = risk['title']
        conn.execute("DELETE FROM ethical_risks WHERE id = ?", (risk_id,))
        log_activity(conn, p_id, 'RISK_DELETED', f"Risk '{r_title}' removed.")
        conn.commit()
        flash(f"Risk '{r_title}' deleted.", 'success')
    conn.close()
    return redirect(url_for('risks', project_id=p_id if risk else None))

# ----------------- ETHICS GATE REVIEW -----------------
@app.route('/gates')
def gates():
    conn = get_db()
    projects = conn.execute("SELECT * FROM projects ORDER BY id ASC").fetchall()
    project_id = request.args.get('project_id', type=int)
    if not project_id and projects:
        project_id = projects[0]['id']

    current_project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    stages = conn.execute("SELECT * FROM lifecycle_stages WHERE project_id = ? ORDER BY stage_order ASC", (project_id,)).fetchall()
    risks = conn.execute("SELECT * FROM ethical_risks WHERE project_id = ?", (project_id,)).fetchall()
    gates_history = conn.execute(
        """SELECT g.*, p.name as project_name
           FROM ethics_gates g
           JOIN projects p ON g.project_id = p.id
           WHERE g.project_id = ?
           ORDER BY g.id DESC""", (project_id,)
    ).fetchall()

    actions = conn.execute("SELECT * FROM corrective_actions WHERE project_id = ? ORDER BY id DESC", (project_id,)).fetchall()
    conn.close()

    return render_template(
        'ethics_gate.html',
        projects=projects,
        project=current_project,
        stages=stages,
        risks=risks,
        gates_history=gates_history,
        actions=actions
    )

@app.route('/api/gates/review', methods=['POST'])
def submit_gate_review():
    project_id = request.form.get('project_id', type=int)
    stage_name = request.form.get('stage_name', '').strip()
    reviewer_name = request.form.get('reviewer_name', '').strip()
    reviewer_role = request.form.get('reviewer_role', '').strip()
    risks_reviewed = request.form.get('risks_reviewed', '').strip()
    evidence_reviewed = request.form.get('evidence_reviewed', '').strip()
    review_notes = request.form.get('review_notes', '').strip()
    decision = request.form.get('decision', '').strip()
    conditions = request.form.get('conditions', '').strip()
    required_actions = request.form.get('required_actions', '').strip()
    action_owner = request.form.get('action_owner', '').strip()
    target_completion_date = request.form.get('target_completion_date', '').strip()
    review_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if not project_id or not stage_name or not reviewer_name or not decision or not review_notes:
        flash('Project, Stage, Reviewer, Review Notes, and Gate Decision are required.', 'danger')
        return redirect(url_for('gates', project_id=project_id))

    # Decision rule validations
    if decision == 'Proceed with Conditions' and not conditions:
        flash('A documented condition is mandatory when selecting "Proceed with Conditions".', 'danger')
        return redirect(url_for('gates', project_id=project_id))

    if decision == 'Remediate and Review Again' and not required_actions:
        flash('Documented required corrective actions are mandatory when selecting "Remediate and Review Again".', 'danger')
        return redirect(url_for('gates', project_id=project_id))

    conn = get_db()
    cur = conn.cursor()

    cur.execute('''
        INSERT INTO ethics_gates (
            project_id, stage_name, reviewer_name, reviewer_role, risks_reviewed,
            evidence_reviewed, review_notes, decision, conditions, required_actions,
            action_owner, target_completion_date, review_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        project_id, stage_name, reviewer_name, reviewer_role, risks_reviewed,
        evidence_reviewed, review_notes, decision, conditions, required_actions,
        action_owner, target_completion_date, review_date
    ))
    gate_id = cur.lastrowid

    # Update Stage & Project Status based on Gate Decision
    if decision == 'Proceed':
        cur.execute(
            "UPDATE lifecycle_stages SET status = 'Passed Gate', completed_at = ? WHERE project_id = ? AND stage_name = ?",
            (review_date, project_id, stage_name)
        )
        cur.execute("UPDATE projects SET status = 'Active' WHERE id = ?", (project_id,))
        # advance stage if applicable
        current_stage_row = cur.execute(
            "SELECT stage_order FROM lifecycle_stages WHERE project_id = ? AND stage_name = ?",
            (project_id, stage_name)
        ).fetchone()
        if current_stage_row and current_stage_row['stage_order'] < 6:
            next_order = current_stage_row['stage_order'] + 1
            next_stage = cur.execute(
                "SELECT stage_name FROM lifecycle_stages WHERE project_id = ? AND stage_order = ?",
                (project_id, next_order)
            ).fetchone()
            if next_stage:
                cur.execute(
                    "UPDATE lifecycle_stages SET status = 'In Progress' WHERE project_id = ? AND stage_order = ? AND status = 'Pending'",
                    (project_id, next_order)
                )
                cur.execute("UPDATE projects SET current_stage = ? WHERE id = ?", (next_stage['stage_name'], project_id))

    elif decision == 'Proceed with Conditions':
        cur.execute(
            "UPDATE lifecycle_stages SET status = 'Passed Gate', evidence_notes = evidence_notes || ' [Conditions: ' || ? || ']', completed_at = ? WHERE project_id = ? AND stage_name = ?",
            (conditions, review_date, project_id, stage_name)
        )
        cur.execute("UPDATE projects SET status = 'Active' WHERE id = ?", (project_id,))
        # Also create a corrective action / condition tracker
        cur.execute('''
            INSERT INTO corrective_actions (project_id, gate_id, action_title, description, assigned_to, due_date, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'Open', ?)
        ''', (project_id, gate_id, f"Condition: {stage_name}", conditions, action_owner or reviewer_name, target_completion_date, review_date))

    elif decision == 'Remediate and Review Again':
        cur.execute(
            "UPDATE lifecycle_stages SET status = 'Remediating' WHERE project_id = ? AND stage_name = ?",
            (project_id, stage_name)
        )
        cur.execute("UPDATE projects SET status = 'Remediating', current_stage = ? WHERE id = ?", (stage_name, project_id))
        # Insert corrective action
        cur.execute('''
            INSERT INTO corrective_actions (project_id, gate_id, action_title, description, assigned_to, due_date, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'Open', ?)
        ''', (project_id, gate_id, f"Remediation: {stage_name}", required_actions, action_owner or 'Unassigned', target_completion_date, review_date))

    elif decision == 'Stop or Escalate':
        cur.execute(
            "UPDATE lifecycle_stages SET status = 'Blocked' WHERE project_id = ? AND stage_name = ?",
            (project_id, stage_name)
        )
        cur.execute("UPDATE projects SET status = 'Suspended', current_stage = ? WHERE id = ?", (stage_name, project_id))

    log_activity(conn, project_id, 'GATE_DECISION', f"Ethics Gate decision for {stage_name}: '{decision}' by {reviewer_name}.")
    conn.commit()
    conn.close()

    flash(f"Ethics Gate Review submitted successfully. Decision recorded: '{decision}'.", 'success')
    return redirect(url_for('gates', project_id=project_id))

# ----------------- FIVE PILLAR ASSESSMENT -----------------
@app.route('/pillars')
def pillars():
    conn = get_db()
    projects = conn.execute("SELECT * FROM projects ORDER BY id ASC").fetchall()
    project_id = request.args.get('project_id', type=int)
    if not project_id and projects:
        project_id = projects[0]['id']

    current_project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    pillars_list = conn.execute("SELECT * FROM pillar_assessments WHERE project_id = ? ORDER BY id ASC", (project_id,)).fetchall()
    risks = conn.execute("SELECT * FROM ethical_risks WHERE project_id = ?", (project_id,)).fetchall()

    pillars_data = []
    completed_count = 0
    total_count = len(pillars_list)

    for p in pillars_list:
        p_dict = dict(p)
        try:
            p_dict['questions'] = json.loads(p['checklist_data'] or '[]')
        except:
            p_dict['questions'] = []

        # Find linked risks for this pillar
        p_dict['linked_risks'] = [
            r for r in risks if p['pillar_name'].lower() in r['pillar'].lower() or p['pillar_code'] == r['pillar']
        ]
        if p['status'] == 'Completed':
            completed_count += 1
        pillars_data.append(p_dict)

    conn.close()
    return render_template(
        'pillars.html',
        projects=projects,
        project=current_project,
        pillars=pillars_data,
        completed_count=completed_count,
        total_count=total_count
    )

@app.route('/api/pillars/<int:pillar_id>/save', methods=['POST'])
def save_pillar(pillar_id):
    conn = get_db()
    pillar = conn.execute("SELECT * FROM pillar_assessments WHERE id = ?", (pillar_id,)).fetchone()
    if not pillar:
        conn.close()
        flash('Pillar assessment not found.', 'danger')
        return redirect(url_for('pillars'))

    status = request.form.get('status', pillar['status'])
    evidence_notes = request.form.get('evidence_notes', pillar['evidence_notes'])

    try:
        current_questions = json.loads(pillar['checklist_data'] or '[]')
    except:
        current_questions = []

    for idx, q in enumerate(current_questions):
        q['done'] = (request.form.get(f'q_{idx}') == 'on')

    completed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if status == 'Completed' else pillar['completed_at']

    conn.execute('''
        UPDATE pillar_assessments
        SET status = ?, evidence_notes = ?, checklist_data = ?, completed_at = ?
        WHERE id = ?
    ''', (status, evidence_notes, json.dumps(current_questions), completed_at, pillar_id))

    log_activity(conn, pillar['project_id'], 'PILLAR_ASSESSMENT', f"Pillar [{pillar['pillar_code']}] '{pillar['pillar_name']}' updated (Status: {status}).")
    conn.commit()
    conn.close()

    flash(f"Assessment for [{pillar['pillar_code']}] {pillar['pillar_name']} saved successfully.", 'success')
    return redirect(url_for('pillars', project_id=pillar['project_id']))

# ----------------- MONITORING AND ACCOUNTABILITY -----------------
@app.route('/monitoring')
def monitoring():
    conn = get_db()
    projects = conn.execute("SELECT * FROM projects ORDER BY id ASC").fetchall()
    project_id = request.args.get('project_id', type=int)
    if not project_id and projects:
        project_id = projects[0]['id']

    current_project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    incidents_list = conn.execute(
        """SELECT i.*, p.name as project_name
           FROM incidents i
           JOIN projects p ON i.project_id = p.id
           WHERE i.project_id = ?
           ORDER BY i.id DESC""", (project_id,)
    ).fetchall()

    actions = conn.execute("SELECT * FROM corrective_actions WHERE project_id = ? ORDER BY id DESC", (project_id,)).fetchall()
    stages = conn.execute("SELECT * FROM lifecycle_stages WHERE project_id = ? ORDER BY stage_order ASC", (project_id,)).fetchall()

    conn.close()
    return render_template(
        'monitoring.html',
        projects=projects,
        project=current_project,
        incidents=incidents_list,
        actions=actions,
        stages=stages
    )

@app.route('/api/incidents/create', methods=['POST'])
def create_incident():
    project_id = request.form.get('project_id', type=int)
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    incident_type = request.form.get('incident_type', 'User Complaint').strip()
    severity = request.form.get('severity', 'Moderate').strip()
    pillar_impacted = request.form.get('pillar_impacted', 'Continuous Accountability').strip()
    reported_by = request.form.get('reported_by', '').strip()
    remediation_notes = request.form.get('remediation_notes', '').strip()
    reopen_stage = request.form.get('reopen_stage', '').strip()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if not project_id or not title or not description or not reported_by:
        flash('Project, Title, Description, and Reporter are mandatory.', 'danger')
        return redirect(url_for('monitoring', project_id=project_id))

    conn = get_db()
    cur = conn.cursor()

    cur.execute('''
        INSERT INTO incidents (
            project_id, title, description, incident_type, severity, pillar_impacted,
            reported_by, date_reported, remediation_notes, status, reopened_stage
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Open', ?)
    ''', (
        project_id, title, description, incident_type, severity, pillar_impacted,
        reported_by, now, remediation_notes, reopen_stage if reopen_stage else None
    ))

    # If serious incident and stage reopening requested
    if reopen_stage and severity in ['Moderate', 'Serious/Critical']:
        cur.execute(
            "UPDATE lifecycle_stages SET status = 'Remediating', evidence_notes = evidence_notes || ' [Reopened due to incident: ' || ? || ']' WHERE project_id = ? AND stage_name = ?",
            (title, project_id, reopen_stage)
        )
        cur.execute("UPDATE projects SET status = 'Remediating', current_stage = ? WHERE id = ?", (reopen_stage, project_id))
        log_activity(conn, project_id, 'STAGE_REOPENED', f"Critical incident '{title}' triggered reopening of stage '{reopen_stage}'.")

    log_activity(conn, project_id, 'INCIDENT_RECORDED', f"Incident recorded: '{title}' ({severity}) by {reported_by}.")
    conn.commit()
    conn.close()

    flash(f"Incident '{title}' recorded successfully.", 'success')
    return redirect(url_for('monitoring', project_id=project_id))

@app.route('/api/incidents/<int:incident_id>/status', methods=['POST'])
def update_incident_status(incident_id):
    conn = get_db()
    incident = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
    if not incident:
        conn.close()
        flash('Incident not found.', 'danger')
        return redirect(url_for('monitoring'))

    status = request.form.get('status', incident['status'])
    notes = request.form.get('remediation_notes', incident['remediation_notes'])

    conn.execute('''
        UPDATE incidents
        SET status = ?, remediation_notes = ?
        WHERE id = ?
    ''', (status, notes, incident_id))

    log_activity(conn, incident['project_id'], 'INCIDENT_UPDATED', f"Incident #{incident_id} '{incident['title']}' updated to '{status}'.")
    conn.commit()
    conn.close()

    flash('Incident status updated.', 'success')
    return redirect(url_for('monitoring', project_id=incident['project_id']))

@app.route('/api/corrective-actions/<int:action_id>/update', methods=['POST'])
def update_corrective_action(action_id):
    conn = get_db()
    action = conn.execute("SELECT * FROM corrective_actions WHERE id = ?", (action_id,)).fetchone()
    if not action:
        conn.close()
        flash('Corrective action not found.', 'danger')
        return redirect(url_for('monitoring'))

    status = request.form.get('status', action['status'])
    resolution_notes = request.form.get('resolution_notes', action['resolution_notes'])

    conn.execute('''
        UPDATE corrective_actions
        SET status = ?, resolution_notes = ?
        WHERE id = ?
    ''', (status, resolution_notes, action_id))

    log_activity(conn, action['project_id'], 'ACTION_UPDATED', f"Corrective Action #{action_id} '{action['action_title']}' updated to '{status}'.")
    conn.commit()
    conn.close()

    flash('Corrective action updated.', 'success')
    return redirect(url_for('monitoring', project_id=action['project_id']))

# ----------------- REPORTS AND EXPORTS -----------------
@app.route('/reports')
def reports():
    conn = get_db()
    projects = conn.execute("SELECT * FROM projects ORDER BY id ASC").fetchall()
    project_id = request.args.get('project_id', type=int)
    if not project_id and projects:
        project_id = projects[0]['id']

    current_project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    stages = conn.execute("SELECT * FROM lifecycle_stages WHERE project_id = ? ORDER BY stage_order ASC", (project_id,)).fetchall()
    pillars = conn.execute("SELECT * FROM pillar_assessments WHERE project_id = ? ORDER BY id ASC", (project_id,)).fetchall()
    risks = conn.execute("SELECT * FROM ethical_risks WHERE project_id = ? ORDER BY risk_score DESC", (project_id,)).fetchall()
    gates = conn.execute("SELECT * FROM ethics_gates WHERE project_id = ? ORDER BY id DESC", (project_id,)).fetchall()
    actions = conn.execute("SELECT * FROM corrective_actions WHERE project_id = ? ORDER BY id DESC", (project_id,)).fetchall()
    incidents = conn.execute("SELECT * FROM incidents WHERE project_id = ? ORDER BY id DESC", (project_id,)).fetchall()

    conn.close()
    return render_template(
        'reports.html',
        projects=projects,
        project=current_project,
        stages=stages,
        pillars=pillars,
        risks=risks,
        gates=gates,
        actions=actions,
        incidents=incidents
    )

@app.route('/reports/<int:project_id>/export/pdf')
def export_pdf(project_id):
    conn = get_db()
    project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not project:
        conn.close()
        flash('Project not found.', 'danger')
        return redirect(url_for('reports'))

    stages = conn.execute("SELECT * FROM lifecycle_stages WHERE project_id = ? ORDER BY stage_order ASC", (project_id,)).fetchall()
    pillars = conn.execute("SELECT * FROM pillar_assessments WHERE project_id = ? ORDER BY id ASC", (project_id,)).fetchall()
    risks = conn.execute("SELECT * FROM ethical_risks WHERE project_id = ? ORDER BY risk_score DESC", (project_id,)).fetchall()
    gates = conn.execute("SELECT * FROM ethics_gates WHERE project_id = ? ORDER BY id DESC", (project_id,)).fetchall()
    actions = conn.execute("SELECT * FROM corrective_actions WHERE project_id = ? ORDER BY id DESC", (project_id,)).fetchall()
    incidents = conn.execute("SELECT * FROM incidents WHERE project_id = ? ORDER BY id DESC", (project_id,)).fetchall()
    conn.close()

    pdf_bytes = report_generator.build_pdf_report(project, stages, pillars, risks, gates, actions, incidents)
    filename = f"ETHIC-Loop-Report-Project-{project_id}.pdf"

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )

@app.route('/reports/<int:project_id>/export/csv')
def export_csv(project_id):
    export_type = request.args.get('type', 'summary')
    conn = get_db()
    project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not project:
        conn.close()
        flash('Project not found.', 'danger')
        return redirect(url_for('reports'))

    risks = conn.execute("SELECT * FROM ethical_risks WHERE project_id = ? ORDER BY risk_score DESC", (project_id,)).fetchall()

    if export_type == 'risks':
        csv_data = report_generator.build_risks_csv(risks)
        filename = f"ETHIC-Loop-Risk-Register-Project-{project_id}.csv"
    else:
        stages = conn.execute("SELECT * FROM lifecycle_stages WHERE project_id = ? ORDER BY stage_order ASC", (project_id,)).fetchall()
        gates = conn.execute("SELECT * FROM ethics_gates WHERE project_id = ? ORDER BY id DESC", (project_id,)).fetchall()
        incidents = conn.execute("SELECT * FROM incidents WHERE project_id = ? ORDER BY id DESC", (project_id,)).fetchall()
        csv_data = report_generator.build_summary_csv(project, stages, risks, gates, incidents)
        filename = f"ETHIC-Loop-Project-Summary-{project_id}.csv"

    conn.close()

    response = make_response(csv_data)
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    response.headers["Content-type"] = "text/csv; charset=utf-8"
    return response

# ----------------- DEMONSTRATION SCENARIO -----------------
@app.route('/demo-scenario')
def demo_scenario():
    conn = get_db()
    # Find AI Recruitment System project
    recruitment_project = conn.execute(
        "SELECT * FROM projects WHERE name LIKE '%Recruitment%' LIMIT 1"
    ).fetchone()

    if not recruitment_project:
        # Fallback to first project
        recruitment_project = conn.execute("SELECT * FROM projects LIMIT 1").fetchone()

    p_id = recruitment_project['id'] if recruitment_project else None
    stages = conn.execute("SELECT * FROM lifecycle_stages WHERE project_id = ? ORDER BY stage_order ASC", (p_id,)).fetchall() if p_id else []
    risks = conn.execute("SELECT * FROM ethical_risks WHERE project_id = ? ORDER BY risk_score DESC", (p_id,)).fetchall() if p_id else []
    gates = conn.execute("SELECT * FROM ethics_gates WHERE project_id = ? ORDER BY id DESC", (p_id,)).fetchall() if p_id else []
    actions = conn.execute("SELECT * FROM corrective_actions WHERE project_id = ? ORDER BY id DESC", (p_id,)).fetchall() if p_id else []
    incidents = conn.execute("SELECT * FROM incidents WHERE project_id = ? ORDER BY id DESC", (p_id,)).fetchall() if p_id else []

    conn.close()

    return render_template(
        'demo_scenario.html',
        project=recruitment_project,
        stages=stages,
        risks=risks,
        gates=gates,
        actions=actions,
        incidents=incidents
    )

@app.route('/api/demo/execute-step', methods=['POST'])
def execute_demo_step():
    data = request.json or {}
    step = data.get('step')
    project_id = data.get('project_id')

    conn = get_db()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if step == 7:  # Step 7: Verification and retesting signoff
        adequacy = data.get('adequacy', 'Adequate')
        notes = data.get('verification_notes',
            'Reviewer verified empirical retest results: Disparate impact ratio increased from 0.61 to 0.89 (four-fifths benchmark met). PII redaction filters confirmed operational. Corrective action verified as adequate.'
        )
        # Update fairness risk
        conn.execute('''
            UPDATE ethical_risks
            SET mitigation_strategy = ?,
                status = 'Under Review',
                updated_at = ?
            WHERE project_id = ? AND title LIKE '%screening%'
        ''', (f"Empirical Retest Findings: {notes}", now, project_id))

        # Update corrective action
        conn.execute('''
            UPDATE corrective_actions
            SET status = 'Verified & Closed',
                resolution_notes = ?
            WHERE project_id = ? AND action_title LIKE '%Demographic%'
        ''', (f"Verification Outcome ({adequacy}): {notes}", project_id))

        log_activity(conn, project_id, 'ETHICAL_VERIFICATION', f"Step 7: Verification & retest findings recorded as '{adequacy}'.")
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'Verification evidence recorded successfully! Corrective action marked as {adequacy}.'})

    elif step == 8:  # Step 8: Final Ethics Gate review decision
        decision = data.get('decision', 'Proceed with Conditions')
        conditions = data.get('conditions',
            'Mandatory monthly statistical parity audit report submission and mandatory recruiter double-blind inspection for any candidate score within 15% of acceptance threshold.'
        )
        review_notes = data.get('review_notes',
            'Testing stage ethical verification complete. Empirical debiasing evidence verified with 0.89 disparate impact ratio across protected demographic cohorts. Authorized advancement to Deployment subject to post-deployment continuous accountability covenants.'
        )
        reviewer_name = data.get('reviewer_name', 'Dr. Sarah Lin')
        reviewer_role = data.get('reviewer_role', 'Lead Ethical Compliance Officer')

        cur = conn.cursor()
        cur.execute('''
            INSERT INTO ethics_gates (
                project_id, stage_name, reviewer_name, reviewer_role, risks_reviewed,
                evidence_reviewed, review_notes, decision, conditions, required_actions,
                action_owner, target_completion_date, review_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            project_id, 'Testing', reviewer_name, reviewer_role,
            'AI Resume Screening Fairness Risk (Score 20 mitigated via debiased re-weighting); Human oversight on borderline candidates',
            'Audited debiasing test run #208: 0.89 four-fifths rule compliance achieved; WCAG 2.1 AA screen-reader compatibility certified.',
            review_notes,
            decision,
            conditions if 'Conditions' in decision else None,
            None,
            'Elena Vance (Ethics Chair)',
            '2026-12-15',
            now
        ))

        if decision == 'Proceed' or decision == 'Proceed with Conditions':
            cur.execute("UPDATE lifecycle_stages SET status = 'Passed Gate', completed_at = ? WHERE project_id = ? AND stage_name = 'Testing'", (now, project_id))
            cur.execute("UPDATE lifecycle_stages SET status = 'In Progress' WHERE project_id = ? AND stage_name = 'Deployment'", (project_id,))
            cur.execute("UPDATE projects SET current_stage = 'Deployment', status = 'Active' WHERE id = ?", (project_id,))
        elif decision == 'Remediate and Review Again':
            cur.execute("UPDATE lifecycle_stages SET status = 'Remediating' WHERE project_id = ? AND stage_name = 'Testing'", (project_id,))
            cur.execute("UPDATE projects SET status = 'Remediating', current_stage = 'Testing' WHERE id = ?", (project_id,))
        elif decision == 'Stop or Escalate':
            cur.execute("UPDATE lifecycle_stages SET status = 'Blocked' WHERE project_id = ? AND stage_name = 'Testing'", (project_id,))
            cur.execute("UPDATE projects SET status = 'Suspended', current_stage = 'Testing' WHERE id = ?", (project_id,))

        log_activity(conn, project_id, 'GATE_DECISION', f"Step 8: Final Ethics Gate decision recorded: '{decision}' by {reviewer_name}.")
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'Ethics Gate Decision recorded: {decision}! Pipeline updated.'})

    elif step == 'reset':  # Reset demonstration scenario
        cur = conn.cursor()
        # Reset project status
        cur.execute("UPDATE projects SET current_stage = 'Testing', status = 'Remediating' WHERE id = ?", (project_id,))
        # Reset stages
        cur.execute("UPDATE lifecycle_stages SET status = 'Remediating', completed_at = NULL WHERE project_id = ? AND stage_name = 'Testing'", (project_id,))
        cur.execute("UPDATE lifecycle_stages SET status = 'Pending', completed_at = NULL WHERE project_id = ? AND stage_name = 'Deployment'", (project_id,))
        # Reset fairness risk
        cur.execute('''
            UPDATE ethical_risks
            SET mitigation_strategy = 'Retrain embeddings with synthetic balancing; perform demographic parity re-weighting; enforce minimum 80% four-fifths rule threshold.',
                status = 'Under Review',
                updated_at = ?
            WHERE project_id = ? AND title LIKE '%screening%'
        ''', (now, project_id))
        # Reset corrective action
        cur.execute('''
            UPDATE corrective_actions
            SET status = 'In Progress',
                resolution_notes = 'Preliminary rescoring shows disparate impact improved to 0.88 in local benchmark. Comprehensive re-audit validation pending.'
            WHERE project_id = ? AND action_title LIKE '%Demographic%'
        ''', (project_id,))
        # Keep only initial Remediate gate review (id minimum for testing stage)
        initial_gate = cur.execute(
            "SELECT id FROM ethics_gates WHERE project_id = ? AND stage_name = 'Testing' ORDER BY id ASC LIMIT 1",
            (project_id,)
        ).fetchone()
        if initial_gate:
            cur.execute("DELETE FROM ethics_gates WHERE project_id = ? AND stage_name = 'Testing' AND id > ?", (project_id, initial_gate['id']))

        log_activity(conn, project_id, 'DEMO_RESET', 'Demonstration scenario reset to initial Remediating state.')
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Demonstration scenario reset to initial state.'})

    conn.close()
    return jsonify({'success': False, 'error': 'Unknown step'})

if __name__ == '__main__':
    # Default local development port
    app.run(debug=True, host='127.0.0.1', port=5000)
