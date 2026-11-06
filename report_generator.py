import io
import csv
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from datetime import datetime

# Color Palette
FOREST = colors.HexColor('#174C3C')
SAGE = colors.HexColor('#A7C4A0')
CREAM = colors.HexColor('#F5F3E9')
CHARCOAL = colors.HexColor('#28352D')
LIGHT_SAGE = colors.HexColor('#E5EFE4')
CRITICAL_RED = colors.HexColor('#B91C1C')
HIGH_AMBER = colors.HexColor('#D97706')
MODERATE_YELLOW = colors.HexColor('#B45309')
LOW_GREEN = colors.HexColor('#15803D')

def build_pdf_report(project, stages, pillars, risks, gates, actions, incidents):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=FOREST,
        alignment=TA_LEFT
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=CHARCOAL
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=FOREST,
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=CHARCOAL
    )

    disclaimer_style = ParagraphStyle(
        'DisclaimerText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11,
        textColor=CHARCOAL
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=TA_LEFT
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=CHARCOAL
    )

    badge_style = ParagraphStyle(
        'BadgeStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7,
        leading=9,
        alignment=TA_CENTER
    )

    story = []

    # Title & Header
    story.append(Paragraph("ETHIC-Loop: Ethical SDLC Framework", title_style))
    story.append(Paragraph(f"Comprehensive Project Audit & Ethical Verification Report &bull; Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", subtitle_style))
    story.append(Spacer(1, 8))

    # Academic Disclaimer Box
    disclaimer_html = (
        "<b>ACADEMIC RESEARCH NOTICE:</b> ETHIC-Loop is a proposed conceptual framework for Computer Ethics pedagogy "
        "and research. It is <u>not</u> an established international standard or an empirically validated methodology. "
        "Low numerical risk scores must never replace independent human moral judgment, multi-stakeholder participation, "
        "and empirical accountability."
    )
    disclaimer_table = Table([[Paragraph(disclaimer_html, disclaimer_style)]], colWidths=[540])
    disclaimer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_SAGE),
        ('BOX', (0, 0), (-1, -1), 1, SAGE),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(disclaimer_table)
    story.append(Spacer(1, 12))

    # Project Information Card
    story.append(Paragraph("1. Project Overview", section_heading))
    proj_data = [
        [Paragraph("<b>Project Name:</b>", body_style), Paragraph(project['name'], body_style),
         Paragraph("<b>Application Domain:</b>", body_style), Paragraph(project['domain'], body_style)],
        [Paragraph("<b>Development Team:</b>", body_style), Paragraph(project['owner'], body_style),
         Paragraph("<b>Current SDLC Stage:</b>", body_style), Paragraph(f"<b>{project['current_stage']}</b>", body_style)],
        [Paragraph("<b>Status:</b>", body_style), Paragraph(f"<b>{project['status']}</b>", body_style),
         Paragraph("<b>Created Date:</b>", body_style), Paragraph(project['created_at'], body_style)],
        [Paragraph("<b>Scope / Description:</b>", body_style), Paragraph(project['description'] or 'N/A', body_style), "", ""]
    ]
    proj_table = Table(proj_data, colWidths=[100, 170, 110, 160])
    proj_table.setStyle(TableStyle([
        ('SPAN', (1, 3), (3, 3)),
        ('BACKGROUND', (0, 0), (-1, -1), CREAM),
        ('BOX', (0, 0), (-1, -1), 0.5, SAGE),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2DFD2')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(proj_table)
    story.append(Spacer(1, 10))

    # 2. SDLC Lifecycle Progress
    story.append(Paragraph("2. SDLC Ethical Lifecycle Progression", section_heading))
    stage_rows = [[
        Paragraph("Stage # & Name", table_header_style),
        Paragraph("Status", table_header_style),
        Paragraph("Assigned Reviewer", table_header_style),
        Paragraph("Ethical Requirements / Checkpoint Notes", table_header_style)
    ]]
    for s in stages:
        stage_rows.append([
            Paragraph(f"<b>{s['stage_order']}. {s['stage_name']}</b>", table_cell_style),
            Paragraph(f"<b>{s['status']}</b>", table_cell_style),
            Paragraph(s['assigned_reviewer'] or 'Unassigned', table_cell_style),
            Paragraph(s['evidence_notes'] or s['ethical_requirements'] or 'N/A', table_cell_style)
        ])
    stage_table = Table(stage_rows, colWidths=[120, 80, 120, 220])
    stage_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), FOREST),
        ('BOX', (0, 0), (-1, -1), 0.5, FOREST),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2DFD2')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, CREAM])
    ]))
    story.append(stage_table)
    story.append(Spacer(1, 10))

    # 3. Five-Pillar Ethical Assessment
    story.append(Paragraph("3. Five Pillars Assessment (E-T-H-I-C)", section_heading))
    pillar_rows = [[
        Paragraph("Pillar Code & Name", table_header_style),
        Paragraph("Status", table_header_style),
        Paragraph("Core Ethical Objective", table_header_style),
        Paragraph("Evidence Summary", table_header_style)
    ]]
    for p in pillars:
        pillar_rows.append([
            Paragraph(f"<b>[{p['pillar_code']}] {p['pillar_name']}</b>", table_cell_style),
            Paragraph(f"<b>{p['status']}</b>", table_cell_style),
            Paragraph(p['purpose'] or 'N/A', table_cell_style),
            Paragraph(p['evidence_notes'] or 'Review pending', table_cell_style)
        ])
    pillar_table = Table(pillar_rows, colWidths=[130, 70, 160, 180])
    pillar_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), FOREST),
        ('BOX', (0, 0), (-1, -1), 0.5, FOREST),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2DFD2')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, CREAM])
    ]))
    story.append(pillar_table)
    story.append(Spacer(1, 10))

    # 4. Ethical Risk Register
    story.append(Paragraph("4. Ethical Risk Register & Scores (L × I)", section_heading))
    risk_rows = [[
        Paragraph("Risk Title & Category", table_header_style),
        Paragraph("Pillar / Stage", table_header_style),
        Paragraph("L &times; I", table_header_style),
        Paragraph("Severity", table_header_style),
        Paragraph("Mitigation Strategy", table_header_style),
        Paragraph("Status", table_header_style)
    ]]
    if risks:
        for r in risks:
            sev = r['severity']
            sev_color = CRITICAL_RED if sev == 'Critical' else (HIGH_AMBER if sev == 'High' else (MODERATE_YELLOW if sev == 'Moderate' else LOW_GREEN))
            risk_rows.append([
                Paragraph(f"<b>{r['title']}</b><br/><font color='#666'>Cat: {r['category']}</font>", table_cell_style),
                Paragraph(f"{r['pillar']}<br/>{r['stage_name']}", table_cell_style),
                Paragraph(f"{r['likelihood']} &times; {r['impact']} = <b>{r['risk_score']}</b>", table_cell_style),
                Paragraph(f"<font color='{sev_color.hexval()}'><b>{sev}</b></font>", table_cell_style),
                Paragraph(r['mitigation_strategy'] or 'N/A', table_cell_style),
                Paragraph(f"<b>{r['status']}</b>", table_cell_style)
            ])
    else:
        risk_rows.append([Paragraph("No risks recorded.", table_cell_style), "", "", "", "", ""])

    risk_table = Table(risk_rows, colWidths=[140, 75, 45, 55, 160, 65])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), FOREST),
        ('BOX', (0, 0), (-1, -1), 0.5, FOREST),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2DFD2')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, CREAM])
    ]))
    story.append(risk_table)
    story.append(Spacer(1, 10))

    # 5. Ethics Gate Review History
    story.append(Paragraph("5. Ethics Gate Review History", section_heading))
    gate_rows = [[
        Paragraph("Stage / Date", table_header_style),
        Paragraph("Reviewer & Role", table_header_style),
        Paragraph("Gate Decision", table_header_style),
        Paragraph("Findings, Conditions & Corrective Mandates", table_header_style)
    ]]
    if gates:
        for g in gates:
            dec = g['decision']
            dec_color = LOW_GREEN if 'Proceed' in dec and 'Conditions' not in dec else (
                HIGH_AMBER if 'Conditions' in dec else (
                    CRITICAL_RED if 'Stop' in dec else colors.HexColor('#854D0E')
                )
            )
            details = f"<b>Notes:</b> {g['review_notes']}"
            if g['conditions']:
                details += f"<br/><b>Conditions:</b> {g['conditions']}"
            if g['required_actions']:
                details += f"<br/><b>Corrective Actions:</b> {g['required_actions']} (Owner: {g['action_owner'] or 'Unassigned'}, Due: {g['target_completion_date'] or 'TBD'})"
            gate_rows.append([
                Paragraph(f"<b>{g['stage_name']}</b><br/>{g['review_date']}", table_cell_style),
                Paragraph(f"<b>{g['reviewer_name']}</b><br/>{g['reviewer_role']}", table_cell_style),
                Paragraph(f"<font color='{dec_color.hexval()}'><b>{dec}</b></font>", table_cell_style),
                Paragraph(details, table_cell_style)
            ])
    else:
        gate_rows.append([Paragraph("No gate reviews completed yet.", table_cell_style), "", "", ""])

    gate_table = Table(gate_rows, colWidths=[90, 110, 110, 230])
    gate_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), FOREST),
        ('BOX', (0, 0), (-1, -1), 0.5, FOREST),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2DFD2')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, CREAM])
    ]))
    story.append(gate_table)
    story.append(Spacer(1, 10))

    # 6. Corrective Actions & Incidents
    story.append(Paragraph("6. Corrective Actions & Post-Deployment Monitoring", section_heading))
    action_rows = [[
        Paragraph("Action Item / Incident", table_header_style),
        Paragraph("Type", table_header_style),
        Paragraph("Assigned / Reporter", table_header_style),
        Paragraph("Status", table_header_style),
        Paragraph("Remediation / Resolution Notes", table_header_style)
    ]]
    for a in actions:
        action_rows.append([
            Paragraph(f"<b>{a['action_title']}</b><br/>{a['description']}", table_cell_style),
            Paragraph("Corrective Action", table_cell_style),
            Paragraph(f"{a['assigned_to']}<br/>Due: {a['due_date'] or 'N/A'}", table_cell_style),
            Paragraph(f"<b>{a['status']}</b>", table_cell_style),
            Paragraph(a['resolution_notes'] or 'Pending resolution', table_cell_style)
        ])
    for inc in incidents:
        action_rows.append([
            Paragraph(f"<b>{inc['title']}</b><br/>{inc['description']}", table_cell_style),
            Paragraph(f"Incident ({inc['severity']})", table_cell_style),
            Paragraph(f"{inc['reported_by']}<br/>{inc['date_reported']}", table_cell_style),
            Paragraph(f"<b>{inc['status']}</b>", table_cell_style),
            Paragraph(inc['remediation_notes'] or 'Investigation ongoing', table_cell_style)
        ])
    if not actions and not incidents:
        action_rows.append([Paragraph("No open corrective actions or recorded incidents.", table_cell_style), "", "", "", ""])

    act_table = Table(action_rows, colWidths=[150, 75, 95, 60, 160])
    act_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), FOREST),
        ('BOX', (0, 0), (-1, -1), 0.5, FOREST),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2DFD2')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, CREAM])
    ]))
    story.append(act_table)
    story.append(Spacer(1, 14))

    # Concluding Academic Signoff
    signoff_text = (
        "<b>Framework Evaluation Note:</b> This document was generated automatically by the ETHIC-Loop Framework engine. "
        "The presence of passing gate decisions or closed risks certifies adherence to the defined internal review process "
        "and does not constitute a warranty of absolute moral or legal safety. Continuous post-deployment accountability "
        "and stakeholder engagement remain mandatory under the ETHIC-Loop Continuous Accountability (C) pillar."
    )
    story.append(Paragraph(signoff_text, disclaimer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def build_risks_csv(risks):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Risk ID', 'Stage', 'Ethical Pillar', 'Category', 'Title',
        'Description', 'Affected Stakeholders', 'Likelihood (1-5)',
        'Impact (1-5)', 'Risk Score (L*I)', 'Severity',
        'Mitigation Strategy', 'Responsible Person', 'Due Date', 'Status'
    ])
    for r in risks:
        writer.writerow([
            r['id'], r['stage_name'], r['pillar'], r['category'], r['title'],
            r['description'], r['affected_stakeholders'], r['likelihood'],
            r['impact'], r['risk_score'], r['severity'],
            r['mitigation_strategy'], r['responsible_person'], r['due_date'], r['status']
        ])
    return output.getvalue()

def build_summary_csv(project, stages, risks, gates, incidents):
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['ETHIC-Loop Project Comprehensive Summary'])
    writer.writerow(['Project ID', project['id']])
    writer.writerow(['Project Name', project['name']])
    writer.writerow(['Domain', project['domain']])
    writer.writerow(['Owner', project['owner']])
    writer.writerow(['Current Stage', project['current_stage']])
    writer.writerow(['Status', project['status']])
    writer.writerow(['Created At', project['created_at']])
    writer.writerow([])

    writer.writerow(['--- SDLC LIFECYCLE STAGES ---'])
    writer.writerow(['Order', 'Stage Name', 'Status', 'Reviewer', 'Evidence Notes'])
    for s in stages:
        writer.writerow([s['stage_order'], s['stage_name'], s['status'], s['assigned_reviewer'], s['evidence_notes']])
    writer.writerow([])

    writer.writerow(['--- ETHICAL RISKS REGISTER ---'])
    writer.writerow(['ID', 'Stage', 'Pillar', 'Title', 'Score', 'Severity', 'Status', 'Mitigation'])
    for r in risks:
        writer.writerow([r['id'], r['stage_name'], r['pillar'], r['title'], r['risk_score'], r['severity'], r['status'], r['mitigation_strategy']])
    writer.writerow([])

    writer.writerow(['--- ETHICS GATE DECISIONS ---'])
    writer.writerow(['ID', 'Stage', 'Reviewer', 'Decision', 'Review Date', 'Notes', 'Conditions', 'Actions'])
    for g in gates:
        writer.writerow([g['id'], g['stage_name'], g['reviewer_name'], g['decision'], g['review_date'], g['review_notes'], g['conditions'], g['required_actions']])
    writer.writerow([])

    writer.writerow(['--- MONITORING INCIDENTS ---'])
    writer.writerow(['ID', 'Title', 'Type', 'Severity', 'Pillar', 'Date', 'Status', 'Notes'])
    for i in incidents:
        writer.writerow([i['id'], i['title'], i['incident_type'], i['severity'], i['pillar_impacted'], i['date_reported'], i['status'], i['remediation_notes']])

    return output.getvalue()
