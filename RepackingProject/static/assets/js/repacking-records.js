
function updateRecordingsStatus(ids, status){
    Array.from(ids).forEach(item => {
        visibleRecords.forEach(r => {
            if (r.id == item)
                r.status = status;
        });
    });
}


document.getElementById('processIDForm').addEventListener('submit', e => {
  e.preventDefault();

  const form = e.target;
  const formData = new FormData(form);
  loadingSpinner1.style.display = 'block';

  const recording_ids = [];
  const chosen = visibleRecords.filter(r => {
        return selectedIds.has(r.id); //&& (parseInt(r.status) == 1 || parseInt(r.status) == 6);
  });

  Array.from(chosen).forEach(item => {
    recording_ids.push(item.id);
  });

  formData.set("recording_ids", recording_ids);

  if (!recording_ids.length) {
      showAlert('Обработка', 'Не выбраны записи для обработки.', 'warning');
      loadingSpinner1.style.display = 'none';
      return;
  }

  fetch(form.action, {
    method: form.method,
    body: formData,
  }).then(response => response.json())
  .then(response => {
    if (!response.success) {
      loadingSpinner1.style.display = 'none';

      if (response.message) {
        showAlert(response.message.title, response.message.text, response.message.type);
      }

      return
    }
    loadingSpinner1.style.display = 'none';
    showAlert('Успешно', 'Запись успешно поставлена в очередь на обработку.', 'success');

    Array.from(response.recordings).forEach(item => {
        visibleRecords.forEach(r => {
            if (r.id == item.record_id)
                r.status = item.status;
        });
    });

    selectedIds.clear();
    renderRecords();
    updateSelectedCount();
  })
  .catch(error => {
      loadingSpinner1.style.display = 'none';
      showAlert('Ошибка', 'Произошла ошибка попробуйте позже.', 'error');
      console.log('Error:', error);
  });
});


document.getElementById('terminateIDForm').addEventListener('submit', e => {
  e.preventDefault();

  const form = e.target;
  const formData = new FormData(form);
  loadingSpinner1.style.display = 'block';

  const recording_ids = [];
  const chosen = visibleRecords.filter(r => {
        return selectedIds.has(r.id);
  });

  Array.from(chosen).forEach(item => {
    recording_ids.push(item.id);
  });

  formData.set("recording_ids", recording_ids);

  if (!recording_ids.length) {
      showAlert('Предупреждение', 'Не выбраны записи для завершения.', 'warning');
      loadingSpinner1.style.display = 'none';
      return;
  }

  fetch(form.action, {
    method: form.method,
    body: formData,
  }).then(response => response.json())
  .then(response => {
    if (!response.success) {
      loadingSpinner1.style.display = 'none';

      if (response.message) {
        showAlert(response.message.title, response.message.text, response.message.type);
      }

      return
    }
    loadingSpinner1.style.display = 'none';
    showAlert('Успешно', 'Выбранные записи успешно завершены.', 'success');

    updateRecordingsStatus(response.recording_ids, 1);

    selectedIds.clear();
    renderRecords();
    updateSelectedCount();
  })
  .catch(error => {
      loadingSpinner1.style.display = 'none';
      showAlert('Ошибка', 'Произошла ошибка попробуйте позже.', 'error');
      console.log('Error:', error);
  });
});


document.getElementById('uploadIDForm').addEventListener('submit', e => {
  e.preventDefault();

  const form = e.target;
  const formData = new FormData(form);
  loadingSpinner1.style.display = 'block';

  const recording_ids = [];
  const chosen = visibleRecords.filter(r => {
        return selectedIds.has(r.id);
  });

  Array.from(chosen).forEach(item => {
    recording_ids.push(item.id);
  });

  formData.set("recording_ids", recording_ids);

  if (!recording_ids.length) {
      showAlert('Предупреждение', 'Не выбраны записи для завершения.', 'warning');
      loadingSpinner1.style.display = 'none';
      return;
  }

  fetch(form.action, {
    method: form.method,
    body: formData,
  }).then(response => response.json())
  .then(response => {
    if (!response.success) {
      loadingSpinner1.style.display = 'none';

      if (response.message) {
        showAlert(response.message.title, response.message.text, response.message.type);
      }

      return
    }
    loadingSpinner1.style.display = 'none';
    showAlert('Успешно', 'Выбранные записи добавлены в очередь на загрузку.', 'success');

    //updateRecordingsStatus(response.recording_ids, 4);

    selectedIds.clear();
    renderRecords();
    updateSelectedCount();
  })
  .catch(error => {
      loadingSpinner1.style.display = 'none';
      showAlert('Ошибка', 'Произошла ошибка попробуйте позже.', 'error');
      console.log('Error:', error);
  });
});