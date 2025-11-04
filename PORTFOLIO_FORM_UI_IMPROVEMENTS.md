# Улучшения формы загрузки портфолио

## Дата изменений
${new Date().toISOString().split('T')[0]}

## Обзор изменений

Внесены улучшения в форму загрузки/редактирования портфолио (`/portfolio/new/` и `/portfolio/edit/<pk>`):

1. **Упрощен интерфейс** - убрано поле "Категории", оставлены только необходимые поля
2. **Добавлены placeholders** во все поля формы для улучшения UX
3. **Реализована зависимость номинаций от выставки** через AJAX
4. **Улучшен внешний вид** - все поля используют Floating Labels (Bootstrap 5)
5. **Унифицирован дизайн** форм создания и редактирования

---

## Изменения в файлах

### 1. `exhibition/forms.py` - PortfolioForm

#### Изменения в `__init__`:
- **Добавлены placeholders** для всех полей:
  - `title`: "Название проекта"
  - `description`: "Описание проекта"
  - `exhibition`: "Выберите выставку"
  - `nominations`: "Выберите номинации для проекта"

- **Для администраторов:**
  - Поле `owner` теперь стандартный select с FloatingField
  - Добавлен `empty_label` и `placeholder` для лучшего UX
  - Поле обязательное для заполнения

- **Для дизайнеров:**
  - Поля `owner` и `status` скрыты (hidden inputs)
  - Показывается имя участника в заголовке
  - Фильтрация выставок только активные/будущие

#### Изменения в `helper` property:
- **Раздельные layout для администраторов и дизайнеров:**

**Администратор видит:**
```python
- FloatingField('owner')          # Выбор участника
- FloatingField('exhibition')     # Выбор выставки
- Field('nominations')            # Множественный выбор номинаций
- FloatingField('title')          # Название проекта
- description                     # Описание (WYSIWYG)
- cover                           # Обложка
- files                           # Загрузка фото
- FloatingField('status')         # Видимость на сайте
- attributes (скрыто)             # Аттрибуты фильтра
- SEO поля (card)                 # Мета-теги
```

**Дизайнер видит:**
```python
- HTML заголовок с именем         # "Участник: Имя"
- owner (hidden)                  # Скрытое поле
- FloatingField('exhibition')     # Выбор выставки
- Field('nominations')            # Множественный выбор номинаций
- files                           # Загрузка фото
- FloatingField('title')          # Название проекта
- description                     # Описание (WYSIWYG)
- cover                           # Обложка
- status (hidden)                 # Скрытое поле
```

#### Изменения в `clean`:
- Поле `categories` всегда очищается (не используется в форме)
- Логика зависимости: если нет выставки → очистить nominations и attributes

---

### 2. `exhibition/views.py`

#### Добавлена новая AJAX view:
```python
@login_required
def get_nominations_for_exhibition(request):
    """ AJAX view для получения номинаций по выбранной выставке """
    exhibition_id = request.GET.get('exhibition_id')
    
    if exhibition_id:
        try:
            exhibition = Exhibitions.objects.get(id=exhibition_id)
            nominations = exhibition.nominations.all().values('id', 'title')
            return JsonResponse({'nominations': list(nominations)})
        except Exhibitions.DoesNotExist:
            return JsonResponse({'nominations': []})
    
    return JsonResponse({'nominations': []})
```

**Назначение:**
- Динамически загружает номинации при выборе выставки
- Возвращает JSON с массивом номинаций: `[{id: 1, title: "..."}, ...]`
- Используется JavaScript в шаблоне upload.html

---

### 3. `exhibition/urls.py`

Добавлен новый URL endpoint:
```python
path('api/get-nominations/', views.get_nominations_for_exhibition, name='get-nominations-url'),
```

**URL:** `/api/get-nominations/?exhibition_id=<id>`
**Метод:** GET
**Параметры:** `exhibition_id` (integer)
**Ответ:** `{"nominations": [{"id": 1, "title": "Название"}, ...]}`

---

### 4. `templates/upload.html`

#### Полностью переписан JavaScript блок:

**Старая версия:** 
- Автокомплит для поля owner с кастомным input и dropdown

**Новая версия:**
- Динамическая загрузка nominations при выборе exhibition
- Сохранение выбранных номинаций при редактировании
- Очистка списка номинаций при снятии выбора выставки

```javascript
document.addEventListener('DOMContentLoaded', function() {
    const exhibitionSelect = document.querySelector('select[name="exhibition"]');
    const nominationsSelect = document.querySelector('select[name="nominations"]');
    
    if (exhibitionSelect && nominationsSelect) {
        // Сохраняем изначально выбранные номинации
        const initialNominations = Array.from(nominationsSelect.selectedOptions)
            .map(opt => opt.value);
        
        exhibitionSelect.addEventListener('change', function() {
            const exhibitionId = this.value;
            
            if (!exhibitionId) {
                nominationsSelect.innerHTML = '';
                return;
            }
            
            // AJAX запрос к новому endpoint
            fetch('/api/get-nominations/?exhibition_id=' + exhibitionId)
                .then(response => response.json())
                .then(data => {
                    nominationsSelect.innerHTML = '';
                    
                    if (data.nominations && data.nominations.length > 0) {
                        data.nominations.forEach(nom => {
                            const option = document.createElement('option');
                            option.value = nom.id;
                            option.textContent = nom.title;
                            
                            // Восстанавливаем выбор при редактировании
                            if (initialNominations.includes(String(nom.id))) {
                                option.selected = true;
                            }
                            
                            nominationsSelect.appendChild(option);
                        });
                    } else {
                        // Нет номинаций для выбранной выставки
                        const option = document.createElement('option');
                        option.value = '';
                        option.textContent = 'Нет доступных номинаций';
                        option.disabled = true;
                        nominationsSelect.appendChild(option);
                    }
                })
                .catch(error => {
                    console.error('Ошибка загрузки номинаций:', error);
                });
        });
        
        // Автозагрузка при открытии формы редактирования
        if (exhibitionSelect.value) {
            exhibitionSelect.dispatchEvent(new Event('change'));
        }
    }
});
```

---

## Логика работы

### Для администратора:

1. Открывает `/portfolio/new/`
2. Видит поля: **Участник**, **Выставка**, **Номинации**, **Фото**, **Название**, **Описание**, **Обложка**, **Статус**, **SEO**
3. Выбирает участника из dropdown списка (обычный select)
4. Выбирает выставку → автоматически загружаются номинации для этой выставки
5. Выбирает одну или несколько номинаций
6. Загружает фото, заполняет остальные поля
7. Сохраняет проект

### Для дизайнера:

1. Открывает `/portfolio/new/`
2. Видит заголовок: "Участник: Имя дизайнера"
3. Видит поля: **Выставка**, **Номинации**, **Фото**, **Название**, **Описание**, **Обложка**
4. Выбирает выставку из списка (только активные) → автоматически загружаются номинации
5. Выбирает номинации (обязательно)
6. Загружает фото (обязательно)
7. Заполняет название и описание
8. Сохраняет проект (автоматически скрывается до модерации администратором)

---

## Схема зависимостей

```
Exhibition (Выставка)
    ↓ M2M
Nominations (Номинации)
    ↓ FK
Categories (Категории) - не используется в форме

Portfolio.exhibition → AJAX → nominations
```

**Важно:** Категории привязаны к номинациям на уровне модели, поэтому их не нужно выбирать в форме загрузки. Они автоматически определяются через выбранные номинации.

---

## UI/UX улучшения

### До изменений:
- ❌ Автокомплит не показывал выпадающий список
- ❌ Placeholder не был floating label
- ❌ Список выставок был пустой
- ❌ Категории показывались в форме (избыточно)
- ❌ Номинации не зависели от выставки
- ❌ Не все поля имели placeholders

### После изменений:
- ✅ Все поля используют Floating Labels (Bootstrap 5)
- ✅ Placeholders во всех input/select полях
- ✅ Список выставок корректно фильтруется
- ✅ Категории скрыты (определяются через номинации)
- ✅ Номинации динамически загружаются при выборе выставки
- ✅ Единый дизайн форм создания и редактирования
- ✅ Поле owner - обычный select с встроенным поиском браузера

---

## Тестирование

### Проверка Django:
```bash
python manage.py check
# System check identified no issues (0 silenced).
```

### Ручное тестирование:

1. **Администратор - создание:**
   - `/portfolio/new/` → видны все поля
   - Выбор owner → работает select с прокруткой
   - Выбор exhibition → загружаются номинации

2. **Администратор - редактирование:**
   - `/portfolio/edit/1` → все данные загружены
   - Выбранные номинации сохранены

3. **Дизайнер - создание:**
   - `/portfolio/new/` → упрощенная форма
   - Только активные выставки
   - Обязательные поля: exhibition, nominations, files

4. **Дизайнер - редактирование:**
   - `/portfolio/edit/1` → может редактировать только свои проекты
   - Форма выглядит идентично созданию

---

## Возможные улучшения

### Опционально (если список участников >100):
Можно добавить Select2 или Tom Select для поля owner:
```html
<link href="https://cdn.jsdelivr.net/npm/tom-select@2/dist/css/tom-select.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/tom-select@2/dist/js/tom-select.complete.min.js"></script>
<script>
new TomSelect('select[name="owner"]', {
    create: false,
    sortField: 'text'
});
</script>
```

### Для больших списков номинаций:
Можно добавить группировку по категориям в AJAX response:
```python
# В views.py
nominations = exhibition.nominations.select_related('category').all()
result = {}
for nom in nominations:
    category = nom.category.title if nom.category else 'Без категории'
    if category not in result:
        result[category] = []
    result[category].append({'id': nom.id, 'title': nom.title})
return JsonResponse({'nominations': result})
```

---

## Совместимость

- **Django:** 4.2.15
- **Python:** 3.12.6
- **Bootstrap:** 5.x (FloatingField из crispy-bootstrap5)
- **Browsers:** Chrome 90+, Firefox 88+, Safari 14+, Edge 90+

---

## Заметки для разработчиков

1. **Не удалять поле categories из модели** - оно используется для группировки номинаций в других частях системы
2. **AJAX endpoint не требует CSRF токена** - используется GET запрос с @login_required
3. **Сохранение выбранных номинаций** - реализовано через сохранение initialNominations в JavaScript
4. **Автоматическое скрытие портфолио дизайнеров** - реализовано в views.py (portfolio.status = False для не-staff пользователей)

---

## Итог

Форма загрузки портфолио теперь имеет:
- Чистый и понятный интерфейс
- Логичную последовательность полей
- Динамическую загрузку зависимых данных
- Единообразный дизайн для всех ролей пользователей
- Улучшенный UX с floating labels и placeholders
