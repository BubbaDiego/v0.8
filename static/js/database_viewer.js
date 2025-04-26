// database_viewer.js

console.log('✅ database_viewer.js loaded');

document.addEventListener('DOMContentLoaded', function () {

  // Assume the backend injects this global JSON object
  const datasets = window.datasets || {};

  const tableSelect = document.getElementById('tableSelect');
  const headerEl = document.getElementById('tableHeader');
  const bodyEl = document.getElementById('tableBody');

  function renderTable(datasetKey) {
    const dataset = datasets[datasetKey];
    if (!dataset) {
      headerEl.innerHTML = '';
      bodyEl.innerHTML = '<tr><td colspan="4" class="text-center">No data available.</td></tr>';
      return;
    }

    // Render Headers
    headerEl.innerHTML = '';
    const headerRow = document.createElement('tr');
    dataset.headers.forEach(header => {
      const th = document.createElement('th');
      th.textContent = header;
      headerRow.appendChild(th);
    });
    headerRow.appendChild(document.createElement('th')).textContent = "Actions";
    headerEl.appendChild(headerRow);

    // Render Rows
    bodyEl.innerHTML = '';
    dataset.rows.forEach(row => {
      const tr = document.createElement('tr');

      const tdRef = document.createElement('td');
      tdRef.textContent = row.id ? row.id.substring(0, 6) : '';
      tr.appendChild(tdRef);

      const tdField1 = document.createElement('td');
      tdField1.textContent = row.field1;
      tr.appendChild(tdField1);

      const tdField2 = document.createElement('td');
      tdField2.textContent = row.field2;
      tr.appendChild(tdField2);

      const tdActions = document.createElement('td');

      const editBtn = document.createElement('button');
      editBtn.className = 'btn btn-sm btn-primary edit-btn';
      editBtn.textContent = 'Edit';
      editBtn.dataset.id = row.id;
      editBtn.dataset.field1 = row.field1;
      editBtn.dataset.field2 = row.field2;
      tdActions.appendChild(editBtn);

      const deleteBtn = document.createElement('button');
      deleteBtn.className = 'btn btn-sm btn-danger ms-2 delete-btn';
      deleteBtn.textContent = 'Delete';
      deleteBtn.dataset.id = row.id;
      deleteBtn.dataset.table = datasetKey;
      tdActions.appendChild(deleteBtn);

      tr.appendChild(tdActions);
      bodyEl.appendChild(tr);
    });

    attachRowEvents();
  }

  function attachRowEvents() {
    document.querySelectorAll('.edit-btn').forEach(button => {
      button.addEventListener('click', function () {
        document.getElementById('editRefId').value = this.dataset.id.substring(0, 6);
        document.getElementById('editFullId').value = this.dataset.id;
        document.getElementById('editField1').value = this.dataset.field1;
        document.getElementById('editField2').value = this.dataset.field2;

        const editModal = new bootstrap.Modal(document.getElementById('editModal'));
        editModal.show();
      });
    });

    document.querySelectorAll('.delete-btn').forEach(button => {
      button.addEventListener('click', function () {
        const id = this.dataset.id;
        const table = this.dataset.table;
        if (confirm(`Delete entry ${id.substring(0, 6)}?`)) {
          fetch('/api/delete_entry', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ table, id })
          })
          .then(r => r.json())
          .then(data => {
            if (data.success) {
              alert('Entry deleted successfully.');
              window.location.reload();
            } else {
              alert('Delete failed: ' + data.error);
            }
          })
          .catch(err => {
            console.error('Delete error:', err);
            alert('Delete error.');
          });
        }
      });
    });
  }

  document.getElementById('saveEditBtn').addEventListener('click', function () {
    const btn = this;
    btn.disabled = true;
    const spinner = document.createElement('span');
    spinner.className = 'saving-spinner';
    btn.appendChild(spinner);

    const table = tableSelect.value;
    const id = document.getElementById('editFullId').value;
    const field1 = document.getElementById('editField1').value;
    const field2 = document.getElementById('editField2').value;

    fetch('/api/update_entry', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ table, id, field1, field2 })
    })
    .then(r => r.json())
    .then(data => {
      if (data.success) {
        alert('Entry updated successfully.');
        window.location.reload();
      } else {
        alert('Update failed: ' + data.error);
      }
    })
    .catch(err => {
      console.error('Update error:', err);
      alert('Update error.');
    })
    .finally(() => {
      btn.disabled = false;
      spinner.remove();
      bootstrap.Modal.getInstance(document.getElementById('editModal')).hide();
    });
  });

  // Initial Table Load
  if (tableSelect) {
    tableSelect.addEventListener('change', function () {
      renderTable(this.value);
    });
    renderTable(tableSelect.value);
  }
});
