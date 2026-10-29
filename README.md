# МячМяч — правовые документы

Статический GitHub Pages сайт RU/EN: HTML/CSS без JavaScript, аналитики,
внешних шрифтов и трекеров. Дата вступления документов в силу: 29 октября 2026.

## Адреса

- https://ball-match.github.io/myachmyach-legal/privacy/
- https://ball-match.github.io/myachmyach-legal/en/privacy/
- https://ball-match.github.io/myachmyach-legal/terms/
- https://ball-match.github.io/myachmyach-legal/en/terms/

Оператор: разработчик приложения «МячМяч». Контакт: hello@ballball.ru.
Реквизиты компании не публикуются. Незаполненных полей нет.

## Редактирование

`content/*.md` и четыре источника в
`../ios-app-prepared/docs/appstore-audit/legal/` должны оставаться идентичными.

```sh
python3 build.py --source-dir ../ios-app-prepared/docs/appstore-audit/legal --updated 2026-10-29
python3 verify.py
```

Без `--source-dir` сборка использует локальный `content/`.
`verify.py` проверяет структуру HTML, точное совпадение текста, локальные ссылки,
отсутствие незаполненных полей, дату и сроки модерации.
`PLACEHOLDERS.md` — генерируемый отчёт, ожидается ноль полей.

Документы содержат утверждённые оператором сроки, а не доказательство настройки
серверных TTL. Проверенные потоки SDK и ограничения проверки описаны в README
первичных источников. Публикация не означает подтверждения соответствия всем
законам или гарантированного одобрения App Review.

## GitHub Pages

Публикация: ветка `main`, каталог `/(root)`; `.nojekyll` отключает Jekyll.
404 использует base path `/myachmyach-legal/`.
Локальный просмотр: `python3 -m http.server 8000`.
