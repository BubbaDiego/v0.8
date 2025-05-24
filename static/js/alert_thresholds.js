window.addEventListener('DOMContentLoaded', () => {
  const saveBtn = document.getElementById('saveAllThresholds');
  if (!saveBtn) return;

  saveBtn.addEventListener('click', async evt => {
    evt.preventDefault();

    const rows = document.querySelectorAll('tr[data-id]');
    const payload = Array.from(rows).map(row => ({
      id: row.dataset.id,
      low: parseFloat(row.querySelector('[name="low"]').value) || 0,
      medium: parseFloat(row.querySelector('[name="medium"]').value) || 0,
      high: parseFloat(row.querySelector('[name="high"]').value) || 0,
      enabled: row.querySelector('[name="enabled"]').checked,
      low_notify: Array.from(row.querySelectorAll('[name="low_notify"]:checked')).map(el => el.value),
      medium_notify: Array.from(row.querySelectorAll('[name="medium_notify"]:checked')).map(el => el.value),
      high_notify: Array.from(row.querySelectorAll('[name="high_notify"]:checked')).map(el => el.value)
    }));

    try {
      const resp = await fetch('/system/alert_thresholds/update_all', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await resp.json();
      if (resp.ok && data.success) {
        if (typeof showToast === 'function') {
          showToast('✅ Alert thresholds updated');
        }
      } else {
        const msg = data.error || resp.statusText;
        if (typeof showToast === 'function') {
          showToast(`❌ Failed to save thresholds: ${msg}`, true);
        }
      }
    } catch (err) {
      if (typeof showToast === 'function') {
        showToast('❌ Error saving thresholds', true);
      }
    }
  });
});
