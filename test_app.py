import os
import unittest
import json
import sqlite3
from app import app
from models import get_db, init_db, calculate_risk_score
import report_generator

class EthicLoopTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_01_risk_calculation_formula(self):
        """Test calculation of Likelihood x Impact and severity thresholds"""
        # Low: 1-4
        score, sev = calculate_risk_score(1, 1)
        self.assertEqual(score, 1)
        self.assertEqual(sev, 'Low')

        score, sev = calculate_risk_score(2, 2)
        self.assertEqual(score, 4)
        self.assertEqual(sev, 'Low')

        # Moderate: 5-9
        score, sev = calculate_risk_score(2, 3)
        self.assertEqual(score, 6)
        self.assertEqual(sev, 'Moderate')

        score, sev = calculate_risk_score(3, 3)
        self.assertEqual(score, 9)
        self.assertEqual(sev, 'Moderate')

        # High: 10-16
        score, sev = calculate_risk_score(2, 5)
        self.assertEqual(score, 10)
        self.assertEqual(sev, 'High')

        score, sev = calculate_risk_score(3, 4)
        self.assertEqual(score, 12)
        self.assertEqual(sev, 'High')

        score, sev = calculate_risk_score(4, 4)
        self.assertEqual(score, 16)
        self.assertEqual(sev, 'High')

        # Critical: 17-25 (Scenario requirement: L=4, I=5 -> 20 Critical)
        score, sev = calculate_risk_score(4, 5)
        self.assertEqual(score, 20)
        self.assertEqual(sev, 'Critical')

        score, sev = calculate_risk_score(5, 5)
        self.assertEqual(score, 25)
        self.assertEqual(sev, 'Critical')

    def test_02_all_pages_render_successfully(self):
        """Test that all primary views return 200 and contain appropriate page signatures"""
        conn = get_db()
        p = conn.execute("SELECT id FROM projects LIMIT 1").fetchone()
        p_id = p['id'] if p else 1
        conn.close()

        routes = [
            ('/', b'ETHIC-Loop'),
            ('/projects', b'Project Management'),
            (f'/projects/{p_id}', b'Project:'),
            ('/workflow', b'SDLC Ethical Stages Progression'),
            (f'/workflow?project_id={p_id}', b'SDLC Ethical Stages Progression'),
            ('/risks', b'Ethical Risk Register'),
            (f'/risks?project_id={p_id}', b'Ethical Risk Register'),
            ('/gates', b'Ethics Gate Checkpoint Review'),
            (f'/gates?project_id={p_id}', b'Ethics Gate Checkpoint Review'),
            ('/pillars', b'Five Pillars Assessment'),
            (f'/pillars?project_id={p_id}', b'Five Pillars Assessment'),
            ('/monitoring', b'Post-Deployment Monitoring'),
            (f'/monitoring?project_id={p_id}', b'Post-Deployment Monitoring'),
            ('/reports', b'Ethical Project Audit Report'),
            (f'/reports?project_id={p_id}', b'Ethical Project Audit Report'),
            ('/demo-scenario', b'AI Recruitment')
        ]

        for route, text in routes:
            res = self.client.get(route)
            self.assertEqual(res.status_code, 200, f"Route {route} failed with {res.status_code}")
            self.assertIn(text, res.data, f"Route {route} did not contain {text}")

    def test_03_project_crud_lifecycle(self):
        """Test creating, viewing, editing, and deleting a project"""
        # Create
        create_res = self.client.post('/projects/create', data={
            'name': 'Autonomous Drone Delivery Unit',
            'domain': 'Robotics / Transportation',
            'owner': 'AeroLogistics Dev',
            'description': 'Automated drone parcel delivery network in urban environments.',
            'current_stage': 'Requirements'
        }, follow_redirects=True)
        self.assertEqual(create_res.status_code, 200)
        self.assertIn(b'Autonomous Drone Delivery Unit', create_res.data)

        # Retrieve created project ID
        conn = get_db()
        p = conn.execute("SELECT * FROM projects WHERE name = 'Autonomous Drone Delivery Unit'").fetchone()
        self.assertIsNotNone(p)
        p_id = p['id']

        # Verify default stages were initialized
        stages = conn.execute("SELECT COUNT(*) FROM lifecycle_stages WHERE project_id = ?", (p_id,)).fetchone()[0]
        self.assertEqual(stages, 6)

        # Verify default pillars were initialized
        pillars = conn.execute("SELECT COUNT(*) FROM pillar_assessments WHERE project_id = ?", (p_id,)).fetchone()[0]
        self.assertEqual(pillars, 5)

        # Edit
        edit_res = self.client.post(f'/projects/{p_id}/edit', data={
            'name': 'Autonomous Drone Delivery Unit (Updated)',
            'domain': 'Robotics / Transportation',
            'owner': 'AeroLogistics Ethics Board',
            'description': 'Updated scope description.',
            'current_stage': 'Design',
            'status': 'Active'
        }, follow_redirects=True)
        self.assertEqual(edit_res.status_code, 200)
        self.assertIn(b'Autonomous Drone Delivery Unit (Updated)', edit_res.data)

        # Delete
        del_res = self.client.post(f'/projects/{p_id}/delete', follow_redirects=True)
        self.assertEqual(del_res.status_code, 200)

        # Verify deleted in DB
        p_check = conn.execute("SELECT * FROM projects WHERE id = ?", (p_id,)).fetchone()
        self.assertIsNone(p_check)
        conn.close()

    def test_04_risk_crud_and_matrix(self):
        """Test logging risk, calculations, edit, and 5x5 matrix filtering"""
        conn = get_db()
        project = conn.execute("SELECT id FROM projects LIMIT 1").fetchone()
        p_id = project['id']
        conn.close()

        # Log new risk (Likelihood 4, Impact 5 -> Score 20 Critical)
        res = self.client.post('/api/risks/create', data={
            'project_id': p_id,
            'title': 'Autonomous Navigation Collision Near Pedestrians',
            'pillar': 'Ethical Impact Assessment',
            'stage_name': 'Testing',
            'category': 'Security',
            'affected_stakeholders': 'Pedestrians, City Residents',
            'likelihood': '4',
            'impact': '5',
            'mitigation_strategy': 'Dual redundant LIDAR sensor fusion with physical brake fail-safe.',
            'responsible_person': 'Robotics Safety Team',
            'due_date': '2026-12-01',
            'status': 'Open'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        conn = get_db()
        risk = conn.execute("SELECT * FROM ethical_risks WHERE title = 'Autonomous Navigation Collision Near Pedestrians'").fetchone()
        self.assertIsNotNone(risk)
        self.assertEqual(risk['risk_score'], 20)
        self.assertEqual(risk['severity'], 'Critical')
        r_id = risk['id']

        # Edit Risk
        edit_res = self.client.post(f'/api/risks/{r_id}/edit', data={
            'title': 'Autonomous Navigation Collision Near Pedestrians',
            'stage_name': 'Testing',
            'pillar': 'Ethical Impact Assessment',
            'category': 'Security',
            'affected_stakeholders': 'Pedestrians',
            'likelihood': '2',
            'impact': '5',
            'mitigation_strategy': 'LIDAR tested with 99.99% pedestrian avoidance.',
            'responsible_person': 'Robotics Safety Team',
            'due_date': '2026-12-01',
            'status': 'Mitigating'
        }, follow_redirects=True)
        self.assertEqual(edit_res.status_code, 200)

        risk_updated = conn.execute("SELECT * FROM ethical_risks WHERE id = ?", (r_id,)).fetchone()
        self.assertEqual(risk_updated['risk_score'], 10)
        self.assertEqual(risk_updated['severity'], 'High')

        # Clean up
        self.client.post(f'/api/risks/{r_id}/delete', follow_redirects=True)
        conn.close()

    def test_05_all_four_gate_decisions(self):
        """Test all four Ethics Gate decisions: Proceed, Proceed with Conditions, Remediate, Stop or Escalate"""
        conn = get_db()
        project = conn.execute("SELECT id FROM projects LIMIT 1").fetchone()
        p_id = project['id']
        conn.close()

        # 1. Proceed with Conditions validation (must have condition)
        res_fail_cond = self.client.post('/api/gates/review', data={
            'project_id': p_id,
            'stage_name': 'Requirements',
            'reviewer_name': 'Dr. Reviewer',
            'reviewer_role': 'Chair',
            'review_notes': 'Notes',
            'decision': 'Proceed with Conditions',
            'conditions': ''
        }, follow_redirects=True)
        self.assertIn(b'documented condition is mandatory', res_fail_cond.data)

        # Valid Proceed with Conditions
        res_cond = self.client.post('/api/gates/review', data={
            'project_id': p_id,
            'stage_name': 'Requirements',
            'reviewer_name': 'Dr. Reviewer',
            'reviewer_role': 'Chair',
            'review_notes': 'Approved with oversight condition',
            'decision': 'Proceed with Conditions',
            'conditions': 'Quarterly audit submission mandatory',
            'action_owner': 'Compliance Team',
            'target_completion_date': '2026-12-31'
        }, follow_redirects=True)
        self.assertEqual(res_cond.status_code, 200)

        # 2. Remediate and Review Again validation (must have required actions)
        res_fail_remed = self.client.post('/api/gates/review', data={
            'project_id': p_id,
            'stage_name': 'Design',
            'reviewer_name': 'Dr. Reviewer',
            'reviewer_role': 'Chair',
            'review_notes': 'Notes',
            'decision': 'Remediate and Review Again',
            'required_actions': ''
        }, follow_redirects=True)
        self.assertIn(b'required corrective actions are mandatory', res_fail_remed.data)

        # Valid Remediate
        res_remed = self.client.post('/api/gates/review', data={
            'project_id': p_id,
            'stage_name': 'Design',
            'reviewer_name': 'Dr. Reviewer',
            'reviewer_role': 'Chair',
            'review_notes': 'Architectural redesign required for explainability',
            'decision': 'Remediate and Review Again',
            'required_actions': 'Add SHAP feature importance wireframe to UI',
            'action_owner': 'UX Architect',
            'target_completion_date': '2026-11-20'
        }, follow_redirects=True)
        self.assertEqual(res_remed.status_code, 200)

        # 3. Stop or Escalate
        res_stop = self.client.post('/api/gates/review', data={
            'project_id': p_id,
            'stage_name': 'Development',
            'reviewer_name': 'Dr. Reviewer',
            'reviewer_role': 'Chair',
            'review_notes': 'Severe fundamental ethical vulnerability identified; halting pipeline',
            'decision': 'Stop or Escalate'
        }, follow_redirects=True)
        self.assertEqual(res_stop.status_code, 200)

        conn = get_db()
        st_dev = conn.execute("SELECT status FROM lifecycle_stages WHERE project_id = ? AND stage_name = 'Development'", (p_id,)).fetchone()
        self.assertEqual(st_dev['status'], 'Blocked')

        # 4. Proceed
        res_proceed = self.client.post('/api/gates/review', data={
            'project_id': p_id,
            'stage_name': 'Development',
            'reviewer_name': 'Dr. Reviewer',
            'reviewer_role': 'Chair',
            'review_notes': 'All issues verified and resolved.',
            'decision': 'Proceed'
        }, follow_redirects=True)
        self.assertEqual(res_proceed.status_code, 200)
        st_dev_after = conn.execute("SELECT status FROM lifecycle_stages WHERE project_id = ? AND stage_name = 'Development'", (p_id,)).fetchone()
        self.assertEqual(st_dev_after['status'], 'Passed Gate')
        conn.close()

    def test_06_incident_reporting_and_stage_reopening(self):
        """Test reporting serious incident and triggering lifecycle stage reopening"""
        conn = get_db()
        project = conn.execute("SELECT id FROM projects LIMIT 1").fetchone()
        p_id = project['id']
        conn.close()

        res = self.client.post('/api/incidents/create', data={
            'project_id': p_id,
            'title': 'Severe Unintended Algorithmic Bias in Production Triage',
            'description': 'Patients from rural ZIP codes systematically receiving delayed priority scores.',
            'incident_type': 'Algorithmic Failure',
            'severity': 'Serious/Critical',
            'pillar_impacted': 'Inclusion and Fairness',
            'reported_by': 'Chief Medical Auditor',
            'reopen_stage': 'Testing',
            'remediation_notes': 'Reopening testing stage to retrain geographic distribution weighting.'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Verify stage was reopened to 'Remediating'
        conn = get_db()
        stage = conn.execute("SELECT status, evidence_notes FROM lifecycle_stages WHERE project_id = ? AND stage_name = 'Testing'", (p_id,)).fetchone()
        self.assertEqual(stage['status'], 'Remediating')
        self.assertIn('Reopened due to incident', stage['evidence_notes'])
        conn.close()

    def test_07_pdf_and_csv_export(self):
        """Test PDF and CSV export routes with real DB records"""
        conn = get_db()
        project = conn.execute("SELECT id FROM projects LIMIT 1").fetchone()
        p_id = project['id']
        conn.close()

        # PDF Download
        pdf_res = self.client.get(f'/reports/{p_id}/export/pdf')
        self.assertEqual(pdf_res.status_code, 200)
        self.assertEqual(pdf_res.content_type, 'application/pdf')
        self.assertTrue(pdf_res.data.startswith(b'%PDF-'))

        # Summary CSV Download
        csv_sum_res = self.client.get(f'/reports/{p_id}/export/csv?type=summary')
        self.assertEqual(csv_sum_res.status_code, 200)
        self.assertIn(b'ETHIC-Loop Project Comprehensive Summary', csv_sum_res.data)

        # Risks CSV Download
        csv_risk_res = self.client.get(f'/reports/{p_id}/export/csv?type=risks')
        self.assertEqual(csv_risk_res.status_code, 200)
        self.assertIn(b'Risk ID,Stage,Ethical Pillar', csv_risk_res.data)

    def test_08_demo_scenario_workflow(self):
        """Test Faculty Demonstration 10-step walkthrough execution"""
        conn = get_db()
        p = conn.execute("SELECT id FROM projects WHERE name LIKE '%Recruitment%'").fetchone()
        p_id = p['id']
        conn.close()

        # Step 7: Record retest findings
        step7_res = self.client.post('/api/demo/execute-step', json={'step': 7, 'project_id': p_id})
        self.assertEqual(step7_res.status_code, 200)
        step7_data = json.loads(step7_res.data)
        self.assertTrue(step7_data['success'])

        # Step 8: Gate review approval with conditions
        step8_res = self.client.post('/api/demo/execute-step', json={'step': 8, 'project_id': p_id})
        self.assertEqual(step8_res.status_code, 200)
        step8_data = json.loads(step8_res.data)
        self.assertTrue(step8_data['success'])

        # Verify Stage advanced to Deployment and Gate recorded Proceed with Conditions
        conn = get_db()
        p_updated = conn.execute("SELECT current_stage FROM projects WHERE id = ?", (p_id,)).fetchone()
        self.assertEqual(p_updated['current_stage'], 'Deployment')
        conn.close()

if __name__ == '__main__':
    unittest.main()
