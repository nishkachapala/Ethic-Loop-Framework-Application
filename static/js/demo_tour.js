// ETHIC-Loop Demonstration Walkthrough: AI Recruitment & Resume Screening Verification

async function recordRetestVerification(projectId) {
    const btn = document.getElementById('btn_step_7');
    const adequacy = document.getElementById('step7_adequacy') ? document.getElementById('step7_adequacy').value : 'Adequate';
    const notes = document.getElementById('step7_notes') ? document.getElementById('step7_notes').value : '';

    if (btn) {
        btn.innerHTML = 'Recording Verification...';
        btn.disabled = true;
    }

    try {
        const response = await fetch('/api/demo/execute-step', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                step: 7,
                project_id: projectId,
                adequacy: adequacy,
                verification_notes: notes
            })
        });
        const result = await response.json();
        if (result.success) {
            alert(result.message);
            window.location.reload();
        } else {
            alert('Error: ' + (result.error || 'Execution failed'));
            if (btn) {
                btn.innerHTML = '<i data-lucide="check" style="width:14px;height:14px;"></i> Record Verification Findings';
                btn.disabled = false;
            }
        }
    } catch (e) {
        alert('Server communication error.');
        if (btn) {
            btn.innerHTML = '<i data-lucide="check" style="width:14px;height:14px;"></i> Record Verification Findings';
            btn.disabled = false;
        }
    }
}

async function recordFinalReview(projectId) {
    const btn = document.getElementById('btn_step_8');
    const decision = document.getElementById('step8_decision') ? document.getElementById('step8_decision').value : 'Proceed with Conditions';
    const conditions = document.getElementById('step8_conditions') ? document.getElementById('step8_conditions').value : '';
    const reviewNotes = document.getElementById('step8_notes') ? document.getElementById('step8_notes').value : '';

    if (btn) {
        btn.innerHTML = 'Submitting Gate Review...';
        btn.disabled = true;
    }

    try {
        const response = await fetch('/api/demo/execute-step', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                step: 8,
                project_id: projectId,
                decision: decision,
                conditions: conditions,
                review_notes: reviewNotes
            })
        });
        const result = await response.json();
        if (result.success) {
            alert(result.message);
            window.location.reload();
        } else {
            alert('Error: ' + (result.error || 'Execution failed'));
            if (btn) {
                btn.innerHTML = '<i data-lucide="shield-check" style="width:14px;height:14px;"></i> Record Final Ethics Gate Decision';
                btn.disabled = false;
            }
        }
    } catch (e) {
        alert('Server communication error.');
        if (btn) {
            btn.innerHTML = '<i data-lucide="shield-check" style="width:14px;height:14px;"></i> Record Final Ethics Gate Decision';
            btn.disabled = false;
        }
    }
}

async function resetDemoScenario(projectId) {
    if (!confirm('Reset the AI Recruitment & Resume Screening demonstration scenario back to its initial Remediating state?')) {
        return;
    }

    try {
        const response = await fetch('/api/demo/execute-step', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ step: 'reset', project_id: projectId })
        });
        const result = await response.json();
        if (result.success) {
            alert(result.message);
            window.location.reload();
        } else {
            alert('Reset failed: ' + result.error);
        }
    } catch (e) {
        alert('Communication error while resetting.');
    }
}

// Support legacy function calls if invoked
function runDemoAction(stepNumber, projectId) {
    if (stepNumber === 7) {
        recordRetestVerification(projectId);
    } else if (stepNumber === 8) {
        recordFinalReview(projectId);
    }
}
