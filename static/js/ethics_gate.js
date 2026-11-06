// ETHIC-Loop Ethics Gate Form Validation & Decision Enforcement

document.addEventListener('DOMContentLoaded', function() {
    const decisionSelect = document.getElementById('gate_decision');
    if (decisionSelect) {
        decisionSelect.addEventListener('change', handleGateDecisionChange);
        handleGateDecisionChange();
    }
});

function handleGateDecisionChange() {
    const decision = document.getElementById('gate_decision').value;
    const conditionsGroup = document.getElementById('conditions_group');
    const actionsGroup = document.getElementById('actions_group');
    const escalateAlert = document.getElementById('escalate_alert');

    const conditionsInput = document.getElementById('conditions');
    const requiredActionsInput = document.getElementById('required_actions');

    // Reset visibility
    if (conditionsGroup) conditionsGroup.style.display = 'none';
    if (actionsGroup) actionsGroup.style.display = 'none';
    if (escalateAlert) escalateAlert.style.display = 'none';

    if (conditionsInput) conditionsInput.required = false;
    if (requiredActionsInput) requiredActionsInput.required = false;

    if (decision === 'Proceed with Conditions') {
        if (conditionsGroup) conditionsGroup.style.display = 'block';
        if (conditionsInput) conditionsInput.required = true;
    } else if (decision === 'Remediate and Review Again') {
        if (actionsGroup) actionsGroup.style.display = 'block';
        if (requiredActionsInput) requiredActionsInput.required = true;
    } else if (decision === 'Stop or Escalate') {
        if (escalateAlert) escalateAlert.style.display = 'block';
    }
}
