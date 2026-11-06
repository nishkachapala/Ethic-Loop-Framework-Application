// ETHIC-Loop Ethical Risk Assessment UI Logic

function calculateRisk(lik, imp) {
    const l = parseInt(lik, 10) || 1;
    const i = parseInt(imp, 10) || 1;
    const score = l * i;
    let severity = 'Low';
    let badgeClass = 'badge-risk-Low';

    if (score <= 4) {
        severity = 'Low';
        badgeClass = 'badge-risk-Low';
    } else if (score <= 9) {
        severity = 'Moderate';
        badgeClass = 'badge-risk-Moderate';
    } else if (score <= 16) {
        severity = 'High';
        badgeClass = 'badge-risk-High';
    } else {
        severity = 'Critical';
        badgeClass = 'badge-risk-Critical';
    }
    return { score, severity, badgeClass };
}

function updateRiskCalcPreview(prefix) {
    const likEl = document.getElementById(prefix + '_likelihood');
    const impEl = document.getElementById(prefix + '_impact');
    const scoreEl = document.getElementById(prefix + '_score_preview');
    const sevEl = document.getElementById(prefix + '_severity_preview');

    if (likEl && impEl && scoreEl && sevEl) {
        const { score, severity, badgeClass } = calculateRisk(likEl.value, impEl.value);
        scoreEl.innerText = score;
        sevEl.innerText = severity;
        sevEl.className = 'badge ' + badgeClass;
    }
}

function openEditRiskModal(risk) {
    document.getElementById('edit_risk_id').value = risk.id;
    document.getElementById('edit_risk_form').action = '/api/risks/' + risk.id + '/edit';
    document.getElementById('edit_title').value = risk.title || '';
    document.getElementById('edit_stage_name').value = risk.stage_name || 'Requirements';
    document.getElementById('edit_pillar').value = risk.pillar || 'Ethical Impact Assessment';
    document.getElementById('edit_category').value = risk.category || 'Bias and discrimination';
    document.getElementById('edit_description').value = risk.description || '';
    document.getElementById('edit_affected_stakeholders').value = risk.affected_stakeholders || '';
    document.getElementById('edit_likelihood').value = risk.likelihood || 3;
    document.getElementById('edit_impact').value = risk.impact || 3;
    document.getElementById('edit_mitigation_strategy').value = risk.mitigation_strategy || '';
    document.getElementById('edit_responsible_person').value = risk.responsible_person || '';
    document.getElementById('edit_due_date').value = risk.due_date || '';
    document.getElementById('edit_status').value = risk.status || 'Open';

    updateRiskCalcPreview('edit');
    openModal('editRiskModal');
}

function filterByMatrixCell(likelihood, impact) {
    const rows = document.querySelectorAll('.risk-table-row');
    let matched = 0;
    rows.forEach(row => {
        const rowL = parseInt(row.getAttribute('data-likelihood'), 10);
        const rowI = parseInt(row.getAttribute('data-impact'), 10);
        if (rowL === likelihood && rowI === impact) {
            row.style.display = '';
            matched++;
        } else {
            row.style.display = 'none';
        }
    });

    const filterNotice = document.getElementById('matrixFilterNotice');
    if (filterNotice) {
        filterNotice.innerHTML = `Showing ${matched} risk(s) with Likelihood = ${likelihood} and Impact = ${impact}. <a href="javascript:resetMatrixFilter()" style="color:var(--color-forest);font-weight:700;margin-left:8px;">Reset Filter</a>`;
        filterNotice.style.display = 'block';
    }
}

function resetMatrixFilter() {
    const rows = document.querySelectorAll('.risk-table-row');
    rows.forEach(row => row.style.display = '');
    const filterNotice = document.getElementById('matrixFilterNotice');
    if (filterNotice) filterNotice.style.display = 'none';
}
