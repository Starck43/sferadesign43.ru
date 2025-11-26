import { Modal } from './components/modal.js';

document.addEventListener("DOMContentLoaded", () => {
    const modalContainer = document.getElementById('progressModal');
    const form = document.querySelector('#uploadProjectForm');
    
    if (!form) return;

    const exhibition = form.querySelector('select[name=exhibition]');
    const nominations = form.querySelector('.field-nominations');
    const categories = form.querySelector('.field-categories');
    const attributes = form.querySelector('.field-attributes');
    const images = form.querySelectorAll('.field-images img');
    const files = form.querySelector('input[name=files]');

    // Инициализация видимости полей формы
    if (exhibition?.value === "") {
        nominations?.classList.add('hidden');
        attributes?.classList.add('hidden');
    } else {
        categories?.classList.add('hidden');
    }

    // Обработчик изменения выставки
    exhibition?.addEventListener('change', (e) => {
        if (e.target.value !== "") {
            nominations?.classList.remove('hidden');
            attributes?.classList.remove('hidden');
            categories?.classList.add('hidden');
        } else {
            categories?.classList.remove('hidden');
            attributes?.classList.add('hidden');
            nominations?.classList.add('hidden');
        }
    });

    // Обработчик выбора изображений
    images.forEach((image) => {
        image.addEventListener('click', (e) => {
            e.target.parentNode.classList.toggle('selected');
        });
    });

    // Предварительный просмотр выбранных изображений
    files?.addEventListener('change', (e) => {
        const selectedFiles = e.target.files;
        if (selectedFiles.length > 0) {
            console.log('Выбрано файлов:', selectedFiles.length);
            showFilePreview(selectedFiles);
        }
    });

    // Обработчик отправки формы
    form.addEventListener('submit', (e) => {
        showModal('0%');
        handleFormSubmit(e);
    });

    /**
     * Отображение превью выбранных файлов
     */
    function showFilePreview(fileList) {
        let previewContainer = document.querySelector('.files-preview-container');
        
        if (!previewContainer) {
            previewContainer = document.createElement('div');
            previewContainer.className = 'files-preview-container mt-3';
            files.parentNode.appendChild(previewContainer);
        }

        previewContainer.innerHTML = `
            <p class="text-muted">Выбрано файлов: ${fileList.length}</p>
            <div class="files-preview-grid"></div>
        `;
        
        const previewGrid = previewContainer.querySelector('.files-preview-grid');
        Object.assign(previewGrid.style, {
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(100px, 1fr))',
            gap: '10px',
            marginTop: '10px'
        });

        const maxPreview = Math.min(fileList.length, 10);

        for (let i = 0; i < maxPreview; i++) {
            const file = fileList[i];
            if (file.type.startsWith('image/')) {
                createImagePreview(file, previewGrid);
            }
        }

        if (fileList.length > maxPreview) {
            const moreText = document.createElement('p');
            moreText.className = 'text-muted mt-2';
            moreText.textContent = `... и еще ${fileList.length - maxPreview} файлов`;
            previewContainer.appendChild(moreText);
        }
    }

    /**
     * Создание превью одного изображения
     */
    function createImagePreview(file, container) {
        const previewItem = document.createElement('div');
        previewItem.className = 'file-preview-item';
        Object.assign(previewItem.style, {
            position: 'relative',
            aspectRatio: '1'
        });

        const objectURL = URL.createObjectURL(file);
        const img = document.createElement('img');
        
        Object.assign(img, {
            src: objectURL,
            className: 'img-thumbnail',
            title: file.name
        });
        
        Object.assign(img.style, {
            width: '100%',
            height: '100%',
            objectFit: 'cover'
        });

        img.onload = () => URL.revokeObjectURL(objectURL);
        previewItem.appendChild(img);
        container.appendChild(previewItem);
    }

    /**
     * Показ модального окна с прогрессом
     */
    function showModal(percent) {
        if (!modalContainer) return;

        const bar = modalContainer.querySelector('.progress-bar');
        if (bar) {
            bar.textContent = percent;
        }

        const modal = new Modal(modalContainer);
        modal.show();
    }

    /**
     * Обработка отправки формы через AJAX
     */
    function handleFormSubmit(e) {
        e.preventDefault();
        const data = new FormData(e.target);
        const xhr = new XMLHttpRequest();

        xhr.addEventListener('load', () => {
            handleUploadComplete(xhr);
        });

        xhr.addEventListener('error', (e) => {
            console.error('Ошибка XHR:', e);
            showError('Ошибка загрузки файлов');
        });

        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                updateProgress(e);
            }
        });

        xhr.open(form.method, window.location.href);
        xhr.setRequestHeader('X-REQUESTED-WITH', 'XMLHttpRequest');
        xhr.send(data);
    }

    /**
     * Обновление прогресс-бара
     */
    function updateProgress(e) {
        const progress = (e.loaded / e.total) * 100;
        console.log('Progress:', progress.toFixed(2) + '%');

        if (modalContainer) {
            const bar = modalContainer.querySelector('.progress-bar');
            if (bar) {
                const progressValue = progress.toFixed(2);
                bar.style.width = progressValue + '%';
                bar.setAttribute('aria-valuenow', progressValue);
                bar.textContent = progress.toFixed(0) + '%';
            }
        }
    }

    /**
     * Обработка завершения загрузки
     */
    function handleUploadComplete(xhr) {
        const contentType = xhr.getResponseHeader('Content-Type');

        if (contentType?.indexOf('application/json') !== -1) {
            try {
                const response = JSON.parse(xhr.responseText);

                if (xhr.status >= 200 && xhr.status < 300) {
                    handleSuccessResponse(response);
                } else {
                    handleErrorResponse(response);
                }
            } catch (err) {
                console.error('Ошибка парсинга JSON:', err);
                showError('Ошибка обработки ответа сервера');
            }
        } else if (xhr.status === 0 || xhr.status >= 400) {
            showError('Ошибка соединения с сервером');
        }
    }

    /**
     * Обработка успешного ответа
     */
    function handleSuccessResponse(response) {
        if (response.status === 'success') {
            if (modalContainer) {
                const bar = modalContainer.querySelector('.progress-bar');
                const progressDiv = modalContainer.querySelector('.progress');
                const message = modalContainer.querySelector('.modal-message');
                const footer = modalContainer.querySelector('.modal-footer');
                const title = modalContainer.querySelector('.modal-title');
                
                // Update progress bar to 100%
                if (bar) {
                    bar.style.width = '100%';
                    bar.setAttribute('aria-valuenow', '100');
                    bar.textContent = '100%';
                    bar.classList.remove('progress-bar-animated');
                    bar.classList.add('bg-success');
                }
                
                // Hide progress bar after a moment
                setTimeout(() => {
                    if (progressDiv) {
                        progressDiv.style.display = 'none';
                    }
                }, 500);
                
                // Update title
                if (title) {
                    title.innerHTML = '✓ Загрузка завершена!';
                }
                
                // Show success message
                if (message) {
                    message.innerHTML = `
                        <div class="alert-success">
                            <p><strong>${response.message || 'Портфолио успешно загружено!'}</strong></p>
                            <p class="mb-0">Что делать дальше?</p>
                        </div>
                    `;
                }
                
                // Update footer with action buttons
                if (footer) {
                    footer.innerHTML = `
                        <button type="button" class="btn btn-primary" onclick="window.location.href='/portfolio/new/'">
                            Добавить еще портфолио
                        </button>
                        <button type="button" class="btn btn-outline-primary" onclick="window.location.href='/account/'">
                            Перейти в личный кабинет
                        </button>
                    `;
                }
            }
        }
    }

    /**
     * Обработка ошибки
     */
    function handleErrorResponse(response) {
        if (modalContainer) {
            const message = modalContainer.querySelector('.modal-message');
            if (message) {
                message.innerHTML = `
                    <div class="alert-danger">
                        ${response.message || 'Произошла ошибка при загрузке'}
                    </div>
                `;
            }

            const progressBar = modalContainer.querySelector('.progress');
            if (progressBar) {
                progressBar.style.display = 'none';
            }
        }
        console.error('Ошибка загрузки:', response);
    }

    /**
     * Отображение сообщения об ошибке
     */
    function showError(message) {
        if (modalContainer) {
            const messageEl = modalContainer.querySelector('.modal-message');
            if (messageEl) {
                messageEl.innerHTML = `<div class="alert-danger">${message}</div>`;
            }

            const progressBar = modalContainer.querySelector('.progress');
            if (progressBar) {
                progressBar.style.display = 'none';
            }
        }
    }
});
