
document.getElementById('profileForm').addEventListener('submit', e => {
  e.preventDefault();

  $(`#profileForm input`).removeClass('invalid-input');

  const form = e.target;
  const formData = new FormData(form);

  fetch(form.action, {
      method: form.method,
      body: formData,
  }).then(response => response.json()
  ).then(response => {
    if (!response.success) {
      for (const [field, message] of Object.entries(response.fields)) {
        $(`input[name=${field}]`).parent().children('.invalid-feedback').html(message.join('<br/>'));
        $(`input[name=${field}]`).addClass('invalid-input');
      }
    } else if (response.success && response.redirect){
       window.location.href = response.redirect;
    } else {
      showAlert("Основная информация", "Данные успешно обновленны", "success");
    }
  })
  .catch(error => {
      console.error('Error:', error);
  });
});

// Смена пароля
document.getElementById('passwordForm').addEventListener('submit', e => {
  e.preventDefault();
  $('#passwordForm .invalid-feedback').text('');
  $(`#passwordForm input`).removeClass('invalid-input');

  const form = e.target;
  const formData = new FormData(form);

  const current_password = $("input[name=current_password]").val();
  const password = $("input[name=password]").val();
  const re_password = $("input[name=re_password]").val();
  let message = '';

  if (current_password == password) {
    message = "Пароли не должны быть одинаковыми";
    $(`input[name=current_password]`).parent().children('.invalid-feedback').text(message);
    $(`input[name=password]`).parent().children('.invalid-feedback').text(message);

    $(`input[name=current_password]`).addClass('invalid-input');
    $(`input[name=password]`).addClass('invalid-input');

    return;
  }
  if (password != re_password) {
    message = "Пароли не совпадают";
    $(`input[name=password]`).parent().children('.invalid-feedback').text(message);
    $(`input[name=re_password]`).parent().children('.invalid-feedback').text(message);

    $(`input[name=password]`).addClass('invalid-input');
    $(`input[name=re_password]`).addClass('invalid-input');

    return;
  }

  fetch(form.action, {
      method: form.method,
      body: formData,
  }).then(response => response.json()
  ).then(response => {
    if (!response.success) {
      for (const [field, message] of Object.entries(response.fields)) {
        $(`input[name=${field}]`).parent().children('.invalid-feedback').html(message.join('<br/>'));
        $(`input[name=${field}]`).addClass('invalid-input');
      }
    } else {
      $("input[type=password]").val('');
      showAlert("Изменение пароля", "Пароль успешно изменен", "success");
    }
  })
  .catch(error => {
      console.log('Error:', error);
  });
});

// Переключатель 2FA
document.getElementById('securityForm').addEventListener('submit', e => {
  e.preventDefault();

  const form = e.target;
  const formData = new FormData(form);

  fetch(form.action, {
      method: form.method,
      body: formData,
  }).then(response => response.json()
  ).then(response => {
    if (!response.success) {
      for (const [field, message] of Object.entries(response.fields)) {
        $(`input[name=${field}]`).parent().children('.invalid-feedback').html(message.join('<br/>'));
        $(`input[name=${field}]`).addClass('invalid-input');
      }
    } else {
      showAlert("Безопасноть", "Параметры безопасности успешно изменены", "success");
    }
  })
  .catch(error => {
      console.log('Error:', error);
  });
});
