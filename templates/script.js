document.addEventListener("DOMContentLoaded", function() {
    var fileInput = document.getElementById('fileInput');
    var submitButton = document.getElementById('submitButton');

    // Проверка при изменении состояния инпута
    fileInput.addEventListener('change', function() {
        if (fileInput.files.length > 0) {
            // Активировать кнопку, если файл выбран
            submitButton.disabled = false;
        } else {
            // Деактивировать кнопку, если файл не выбран
            submitButton.disabled = true;
        }
    });

    // Изначально кнопка деактивирована
    submitButton.disabled = true;
});
