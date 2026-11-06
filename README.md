# ETHIC-Loop: Ethical Software Development Lifecycle Framework

**Computer Ethics Academic Research & Capstone Project**  
*Proposed Conceptual Framework for Integrating Ethical Deliberation Across Software Engineering Lifecycles*

> **ACADEMIC NOTICE & DISCLAIMER:**  
> **ETHIC-Loop** is a proposed conceptual framework developed for academic research, pedagogical evaluation, and ethical exploration. It is **not** an established international standard (such as ISO/IEC or IEEE) nor an empirically validated methodology. A low numerical risk score or a passing gate review must never be interpreted as an absolute certification of moral or legal safety. Human moral discernment, continuous stakeholder feedback, and independent oversight remain essential.

---

## 1. Executive Summary & Theoretical Grounding

Contemporary software development methodologies (e.g., Agile, DevOps) heavily optimize for deployment velocity, performance throughput, and feature delivery, often treating ethical, societal, and human-rights considerations as downstream externalities or superficial checklists.

**ETHIC-Loop** introduces a structured, closed-loop governance framework that embeds five foundational ethical pillars into every phase of the traditional six-stage Software Development Life Cycle (SDLC):

### The Five Ethical Pillars (E-T-H-I-C)
1. **E — Ethical Impact Assessment:** Proactive identification and qualitative modeling of societal, psychological, environmental, and individual harms before engineering begins.
2. **T — Transparency and Trust:** Clear documentation of algorithmic design criteria, data provenance, decision explanations, model limitations, and plain-language user disclosures.
3. **H — Human Oversight:** Meaningful human-in-the-loop agency, override capabilities, fallback fail-safes, and accessible human appeal avenues for automated decisions.
4. **I — Inclusion and Fairness:** Elimination of unjust bias, demographic disparity auditing, accessibility conformance (WCAG 2.1 AA), and participatory co-design.
5. **C — Continuous Accountability:** Post-deployment incident triaging, grievance loops, immutable audit trails, and the ability to reopen prior SDLC stages upon emergent harm.

### The Six SDLC Stages
1. **Requirements:** Stakeholder harm modeling, ethical charter drafting, non-goals specification.
2. **Design:** Privacy-by-design, explainability wireframes, human override UX architectures.
3. **Development:** Data hygiene, demographic representation validation, immutable trace logging.
4. **Testing:** Demographic parity testing, statistical disparate impact ratio audits, red-teaming.
5. **Deployment:** Pre-flight transparency cards, operator training, automated drift detection.
6. **Maintenance:** Quarterly fairness re-evaluations, grievance triaging, stage reopening triggers.

---

## 2. The Ethics Gate Decision Model

At each stage boundary, development teams convene an **Ethics Gate Review**. Unlike automated CI/CD linting, the Ethics Gate centers human deliberation and evidence inspection.

The Gate enforces four definitive decisions:
- **Proceed:** Full formal approval with documented evidence. Advances the pipeline to the next lifecycle stage.
- **Proceed with Conditions:** Approval granted subject to binding covenants (e.g., mandatory monthly parity audits, recruiter double-blind review). Requires documented condition text and logs a condition tracking record.
- **Remediate and Review Again:** Halts pipeline progression. Requires specific documented corrective actions, an assigned owner, and target date. Transitions the stage and project status into `Remediating`. A subsequent gate review is mandatory.
- **Stop or Escalate:** Formal pipeline freeze. Freezes the stage as `Blocked` and suspends the project for review by an institutional ethics board or ombudsperson.

---

## 3. Mathematical Risk-Scoring Heuristic

Ethical risks are quantified using a dual-dimensional heuristic:

$$\text{Risk Score} = \text{Likelihood} \times \text{Impact}$$

Where:
- **Likelihood ($L$):** Integer scale from $1$ (Rare) to $5$ (Almost Certain).
- **Impact ($I$):** Integer scale from $1$ (Negligible) to $5$ (Catastrophic Societal Harm).

### Illustrative Classification Thresholds
- **1 – 4:** **Low Risk** (Standard operational monitoring)
- **5 – 9:** **Moderate Risk** (Internal mitigation plan required)
- **10 – 16:** **High Risk** (Mandatory gate deliberation; mitigation signoff required)
- **17 – 25:** **Critical Risk** (Triggers mandatory `Remediate` gate decision; deployment blocked until retested)

*Note: This formula is an illustrative pedagogical heuristic to prioritize engineering effort; it does not represent an actuarial risk probability distribution.*

---

## 4. Technology Stack & Design System

- **Backend:** Python 3.12, Flask 3.1.3
- **Database:** SQLite 3 with parameterized queries, foreign key enforcement, cascading deletes, and persistent schema.
- **Reporting Engine:** ReportLab 5.1.0 (PDF generation) & native CSV export.
- **Frontend:** HTML5, CSS3, Modern Modular JavaScript (ES6+).
- **Visualization:** Chart.js 4.4.1 (dynamic stage bar charts and risk severity doughnuts).
- **Icons:** Lucide Icons.

### Custom Forest & Sage Palette
Conforming to the custom visual palette:
- **Forest (`#174C3C`):** Primary brand identity, sidebar, headings, primary action buttons.
- **Sage (`#A7C4A0`):** Secondary supporting colour, progress bars, chart accents, selected states.
- **Cream (`#F5F3E9`):** Page background, form inputs, light card surfaces.
- **Charcoal (`#28352D`):** Typography, dark footers, high-contrast borders.
- **Accessible Accents:** Amber (`#D97706`) and Red (`#B91C1C`) for critical severity indicators.

---

## 5. Project Directory Structure

```
ce/
├── instance/
│   └── ethic_loop.db         # Persistent SQLite database
├── static/
│   ├── css/
│   │   └── style.css          # Custom Forest & Sage styling, variables & layout
│   └── js/
│       ├── main.js            # UI modals, flash messages, mobile navigation
│       ├── dashboard.js       # Chart.js initialization for stages & severities
│       ├── risks.js           # 5x5 Matrix filtering & real-time L x I calculations
│       ├── ethics_gate.js     # Gate decision validation & condition enforcement
│       └── demo_tour.js       # Faculty demonstration interactive walkthrough engine
├── templates/
│   ├── base.html              # Base shell with sidebar, notice banner & modals
│   ├── dashboard.html         # Live metric cards, charts, and activity log
│   ├── projects.html          # Project listing, search, filtering & deletion
│   ├── project_detail.html    # Detailed project hub
│   ├── workflow.html          # Visual 6-stage SDLC stepper & checklist editor
│   ├── risks.html             # 5x5 Risk Matrix & risk register table
│   ├── ethics_gate.html       # Ethics gate review form & historical audit log
│   ├── pillars.html           # Five pillars (E-T-H-I-C) assessment cards
│   ├── monitoring.html        # Post-deployment incidents & stage reopening
│   ├── reports.html           # Live report preview & PDF/CSV export triggers
│   └── demo_scenario.html     # Dedicated Faculty Guided Demonstration page
├── app.py                     # Main Flask routing, business logic & API endpoints
├── models.py                  # Schema definitions, seed records, and DB connection
├── report_generator.py        # ReportLab PDF building & CSV serialization
├── requirements.txt           # Python package specifications
└── README.md                  # Comprehensive academic documentation
```

---

## 6. Installation & Local Run Instructions

### Prerequisites
- Python 3.10+ (Tested on Python 3.12.10)
- Pip package manager

### Step-by-Step Setup
1. Open PowerShell or Terminal in the project root:
   ```powershell
   cd c:\Users\NISHKA\OneDrive\Desktop\ce
   ```

2. Activate the virtual environment:
   - On Windows (PowerShell):
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - On Windows (CMD):
     ```cmd
     .venv\Scripts\activate.bat
     ```
   - On macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```powershell
   python app.py
   ```
   *(Or using the venv python directly: `.\.venv\Scripts\python.exe app.py`)*

5. Access the application in any web browser:
   ```
   http://127.0.0.1:5000
   ```

---

## 7. AI Recruitment & Resume Screening Verification (Demonstration Guide)

The application includes a realistic demonstration scenario showcasing how ETHIC-Loop structures ethical verification on an automated candidate ranking pipeline:

### 9-Step Verification Workflow:
1. **Project Overview:** Open **AI Recruitment & Resume Screening System** pipeline.
2. **Resume Screening Assessment:** Review how resumes are ingested (PDF/Word), candidate data features utilized, and how shortlisting recommendations are computed via vector similarity against job profiles.
3. **Ethical Risk Identification:** Inspect five mapped vulnerabilities: Biased screening, unauthorized PII access, decision opacity, recruiter automation complacency, and applicant portal accessibility barriers.
4. **Fairness Risk Assessment:** Review the primary bias risk (Likelihood 4 $\times$ Impact 5 = **Score 20, Critical** under the illustrative heuristic thresholds).
5. **Ethics Gate Review Checkpoint:** Inspect the initial Testing stage review where Lead Ethicist Dr. Sarah Lin logged **Remediate and Review Again** due to a 0.61 disparate impact ratio violation.
6. **Corrective Action Mandate:** Review the binding task assigned to ML Engineer Kevin Chen to examine training data, eliminate non-predictive demographic proxies, and apply Fairlearn re-weighting.
7. **Verification & Retesting:** Inspect the team's documented **Evidence and Test Results** (disparate impact improved to 0.89; four-fifths benchmark satisfied). Reviewer records whether corrective actions are adequate.
8. **Final Ethics Gate Decision:** Deliberate and record the final gate decision (**Proceed with Conditions**, with binding monthly auditing covenants).
9. **Verification Report Generation:** Download the official **Verification Report (PDF)** or CSV summary reflecting the real database audit history.

> **Demonstration Boundary Notice:** Candidate profiles and test scores represent simulated sample data. ETHIC-Loop provides the procedural framework for human oversight and evidence review; it does not verify applicant identity, validate genuine credentials, or claim automated proof of zero algorithmic bias.

---

## 8. Known Limitations & Future Work

1. **Subjective Risk Ratings:** Numerical likelihood and impact ratings rely on human estimation, which may vary across different ethical reviewers without standardized calibration rubrics.
2. **Single-Organization Scope:** ETHIC-Loop currently assumes an intra-organizational development team. Multi-tier supply chains and third-party foundation models introduce external dependencies that require extended contractual accountability.
3. **Empirical Evaluation Needed:** Future research must conduct longitudinal controlled studies with practicing engineering teams to measure the effect of gate interventions on software defect rates and societal compliance.
