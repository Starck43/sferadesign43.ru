document.addEventListener("DOMContentLoaded", function () {

    //=include components/_ajax.js

    const modalContainer = document.getElementById('progressModal');
    const form = document.querySelector('#portfolio_form');
    const exhibition = form.querySelector('select[name=exhibition]');
    const nominations = form.querySelector('.field-nominations');
    const categories = form.querySelector('.field-categories');
    const attributes = form.querySelector('.field-attributes');
    const images = form.querySelectorAll('.field-images img');
    const files = form.querySelector('input[name=files]');

    if (exhibition.value === "") {
        nominations && nominations.classList.add('hidden');
        attributes && attributes.classList.add('hidden');
    } else {
        categories && categories.classList.add('hidden');
    }

    exhibition && exhibition.addEventListener('change', function (e) {
        if (e.target.value !== "") {
            nominations && nominations.classList.remove('hidden');
            attributes && attributes.classList.remove('hidden');
            categories && categories.classList.add('hidden');
        } else {
            categories && categories.classList.remove('hidden');
            attributes && attributes.classList.add('hidden');
            nominations && nominations.classList.add('hidden');
        }
    })

    images.forEach(function (image) {
        image.addEventListener('click', function (e) {
            e.target.parentNode.classList.toggle('selected');
        })
    })

    // Предварительный просмотр выбранных изображений
    if (files) {
        files.addEventListener('change', function (e) {
            const selectedFiles = e.target.files;
            if (selectedFiles.length > 0) {
                console.log('Выбрано файлов:', selectedFiles.length);
                showFilePreview(selectedFiles);
            }
        });
    }

    function showFilePreview(fileList) {
        // Создаем или находим контейнер для превью
        let previewContainer = document.querySelector('.files-preview-container');
        if (!previewContainer) {
            previewContainer = document.createElement('div');
            previewContainer.className = 'files-preview-container mt-3';
            files.parentNode.appendChild(previewContainer);
        }

        // Очищаем предыдущие превью
        previewContainer.innerHTML = '<p class="text-muted">Выбрано файлов: ' + fileList.length + '</p><div class="files-preview-grid"></div>';
        const previewGrid = previewContainer.querySelector('.files-preview-grid');

        // Добавляем стили для grid-сетки
        previewGrid.style.display = 'grid';
        previewGrid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(100px, 1fr))';
        previewGrid.style.gap = '10px';
        previewGrid.style.marginTop = '10px';

        // Показываем первые 10 файлов для превью
        const maxPreview = Math.min(fileList.length, 10);

        for (let i = 0; i < maxPreview; i++) {
            const file = fileList[i];
            if (file.type.startsWith('image/')) {
                const previewItem = document.createElement('div');
                previewItem.className = 'file-preview-item';
                previewItem.style.position = 'relative';
                previewItem.style.aspectRatio = '1';

                // Используем IIFE для создания новой области видимости
                (function (currentFile) {
                    const objectURL = URL.createObjectURL(currentFile);

                    const img = document.createElement('img');
                    img.src = objectURL;
                    img.className = 'img-thumbnail';
                    img.style.width = '100%';
                    img.style.height = '100%';
                    img.style.objectFit = 'cover';
                    img.title = currentFile.name;

                    img.onload = function () {
                        URL.revokeObjectURL(objectURL);
                    };

                    previewItem.appendChild(img);
                })(file);

                previewGrid.appendChild(previewItem);
            }
        }

        if (fileList.length > maxPreview) {
            const moreText = document.createElement('p');
            moreText.className = 'text-muted mt-2';
            moreText.textContent = '... и еще ' + (fileList.length - maxPreview) + ' файлов';
            previewContainer.appendChild(moreText);
        }
    }

    form && form.addEventListener('submit', function (e) {
        const html = '0%';
        modalHandler(html);
        ajax(e);
    })


    // Обработчик закрытия всплывающих инфо-окон
    let modalHandler = function (percent) {
        if (modalContainer) {
            modalContainer.addEventListener('show.bs.modal', function () {
                const bar = modalContainer.querySelector('.progress-bar');
                bar.textContent = percent;
            })

            // Правильный вызов show() с опциональными параметрами
            const modal = bootstrap.Modal.getOrCreateInstance(modalContainer);
            modal.show();
        }
    }

    function ajax(e) {
        e.preventDefault();
        const data = new FormData(e.target);
        console.log(data);

        //ajax upload
        const xhr = new XMLHttpRequest();
        console.log(xhr);

        xhr.addEventListener('load', function () {
            let message;
            const content_type = xhr.getResponseHeader('Content-Type');

            // Обработка JSON ответа
            if (content_type && content_type.indexOf('application/json') !== -1) {
                try {
                    const response = JSON.parse(xhr.responseText);

                    if (xhr.status >= 200 && xhr.status < 300) {
                        // Успешная загрузка
                        if (response.status === 'success' && response.location) {
                            // Обновляем прогресс до 100%
                            if (modalContainer) {
                                const bar = modalContainer.querySelector('.progress-bar');
                                message = modalContainer.querySelector('.modal-message');
                                if (bar) {
                                    bar.style.width = '100%';
                                    bar.setAttribute('aria-valuenow', '100');
                                    bar.textContent = '100%';
                                }
                                if (message) {
                                    message.textContent = response.message || 'Загрузка завершена!';
                                }
                            }

                            // Перенаправление через 1 секунду
                            setTimeout(function () {
                                window.location.href = response.location;
                            }, 1000);
                        }
                    } else {
                        // Ошибка валидации или загрузки
                        if (modalContainer) {
                            message = modalContainer.querySelector('.modal-message');
                            if (message) {
                                message.innerHTML = '<div class="alert alert-danger">' +
                                    (response.message || 'Произошла ошибка при загрузке') +
                                    '</div>';
                            }

                            // Скрываем прогресс-бар при ошибке
                            const progressBar = modalContainer.querySelector('.progress');
                            if (progressBar) {
                                progressBar.style.display = 'none';
                            }
                        }
                        console.error('Ошибка загрузки:', response);
                    }
                } catch (err) {
                    console.error('Ошибка парсинга JSON:', err);
                    showError('Ошибка обработки ответа сервера');
                }
            } else if (xhr.status === 0 || xhr.status >= 400) {
                showError('Ошибка соединения с сервером');
            }
        });

        xhr.addEventListener('error', function (e) {
            console.error('Ошибка XHR:', e);
            showError('Ошибка загрузки файлов');
        });

        //The upload progress callback
        xhr.upload.addEventListener('progress', function (e) {
            //The length measurement returns a Boolean value, 100% is false, otherwise true
            if (e.lengthComputable) {
                const progress = (e.loaded / e.total) * 100;
                console.log('Progress:', progress.toFixed(2) + '%');

                // Обновляем прогресс-бар
                if (modalContainer) {
                    const bar = modalContainer.querySelector('.progress-bar');
                    if (bar) {
                        bar.style.width = progress.toFixed(2) + '%';
                        bar.setAttribute('aria-valuenow', progress.toFixed(2));
                        bar.textContent = progress.toFixed(0) + '%';
                    }
                }
            }
        });

        xhr.open(form.method, window.location.href);
        xhr.setRequestHeader('X-REQUESTED-WITH', 'XMLHttpRequest');
        xhr.send(data);
    }

    function showError(message) {
        if (modalContainer) {
            const messageEl = modalContainer.querySelector('.modal-message');
            if (messageEl) {
                messageEl.innerHTML = '<div class="alert alert-danger">' + message + '</div>';
            }
            // Скрываем прогресс-бар при ошибке
            const progressBar = modalContainer.querySelector('.progress');
            if (progressBar) {
                progressBar.style.display = 'none';
            }
        }
    }

})
