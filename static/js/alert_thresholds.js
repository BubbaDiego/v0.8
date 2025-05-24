window.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.save-threshold').forEach(btn => {
    btn.addEventListener('click', async evt => {
      evt.preventDefault();
      const row = btn.closest('tr');
      const id = row.dataset.id;
      const payload = {
        low: parseFloat(row.querySelector('[name="low"]').value) || 0,
        medium: parseFloat(row.querySelector('[name="medium"]').value) || 0,
        high: parseFloat(row.querySelector('[name="high"]').value) || 0,
        enabled: row.querySelector('[name="enabled"]').checked,
        low_notify: Array.from(row.querySelectorAll('[name="low_notify"]:checked')).map(el => el.value),
        medium_notify: Array.from(row.querySelectorAll('[name="medium_notify"]:checked')).map(el => el.value),
        high_notify: Array.from(row.querySelectorAll('[name="high_notify"]:checked')).map(el => el.value)
      };
      try {
        const resp = await fetch(`/system/alert_thresholds/update/${id}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (resp.ok) {
          btn.classList.remove('btn-primary');
          btn.classList.add('btn-success');
          setTimeout(() => {
            btn.classList.remove('btn-success');
            btn.classList.add('btn-primary');
          }, 1000);
        } else {
          alert('Failed to save threshold');
        }
      } catch (err) {
        alert('Error saving threshold');
      }
    });
  });
});
