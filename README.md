# 🎮 MTA Developers Launcher

**MTA Developers Launcher** — это простой лаунчер для Multi Theft Auto, позволяющий легко обновлять, запускать клиент и сервер, а также восстанавливать поврежденные файлы. Он работает в связке с манифестом, создаваемым через `generate_manifest.py`.

---

## 📁 Содержание

- [`launcher.py`](./launcher.py) — графический лаунчер на `tkinter`, который скачивает и обновляет файлы игры, сверяя их хеши с сервером.
- [`generate_manifest.py`](./generate_manifest.py) — утилита для генерации XML-манифеста с контрольными суммами (MD5) всех файлов игры и автоматического обновления версии.

---

## 🔧 Как работает `launcher.py`

`launcher.py` — это основное приложение, предоставляющее GUI, с помощью которого можно:

- Запустить клиент (`Multi Theft Auto.exe`)
- Запустить сервер (`MTA Server.exe`)
- Обновить игру до последней версии
- Восстановить поврежденные или отсутствующие файлы

**Основной функционал:**

- Загружает информацию о последней версии с `version.xml`, размещённого на сервере.
- Сравнивает локальную версию с серверной.
- Если версия устарела — загружает `files_manifest.xml`, в котором перечислены файлы и их хеши.
- Проверяет каждый файл локально, сверяя MD5-хеши.
- Загружает только те файлы, которые отсутствуют или повреждены.
- Поддерживает многопоточную загрузку с отображением скорости и прогресса.

---

## 🛠 Как работает `generate_manifest.py`

Этот скрипт предназначен для разработчиков и запускается на стороне сервера. Он:

1. **Перебирает все файлы в указанной директории**, кроме:
   - самого скрипта
   - `version.xml`
   - `files_manifest.xml`
2. **Вычисляет MD5-хеш** каждого файла.
3. Создаёт `files_manifest.xml` — список всех файлов с их относительным путём и хешем.
4. Обновляет `version.xml`, увеличивая версию (например, с `1.0.3` на `1.0.4`).

**Пример запуска:**

```bash
python generate_manifest.py --folder ./game_files -o files_manifest.xml
```

---

## 📦 Установка и использование

1. **Серверная часть (разработчик):**

   - Разместить `files_manifest.xml` и `version.xml` на веб-сервере.
   - Все файлы игры должны быть доступны по ссылке, соответствующей структуре путей в манифесте.

2. **Клиентская часть (общий доступ к примеру: игроки или разработчики):**

   - Запускает `launcher.py`.
   - Программа автоматически проверяет наличие обновлений и загружает только недостающие или повреждённые файлы.

---

## 💡 Требования

- Python 3.7+
- Модули: `tkinter`, `requests`

---

## 🧑‍💻 Автор

Разработано **e1ectr0venik**  
Версия лаунчера: **v1.1**
