# 🌌 OmniNexus Studio

**Единая экосистема: автономный агент (OpenManus + KODE SDK + II-Agent), голосовая студия Qwen3-TTS (WhiskeyCoder + qwentts.cpp + ComfyUI), шлюз нейросетей OpenClaw (Zero-Token) и управление Android (awesome-android-root + ADB Bridge).**

[English Description Below](#english-description)

---

## 🇷🇺 Описание проекта

**OmniNexus Studio** — это монолитная интегрированная платформа, объединяющая лучшие open-source решения в области автономных ИИ-агентов, синтеза речи нового поколения, конвертации аудиокниг, мульти-модельной маршрутизации без API-токенов и удаленного управления Android-устройствами.

Проект объединяет в единое приложение все репозитории из вашего запроса и дополнен необходимыми ключевыми библиотеками:

### 🧩 Интегрированные репозитории:

1. **`FoundationAgents/OpenManus`** — ядро автономного агента: планирование (ReAct planning loop), разбиение целей на шаги, самопроверка, исполнение bash/терминала, браузерные сценарии, запуск кода и манипуляция файлами.
2. **`shareAI-lab/kode-agent-sdk`** — трёхканальная шина событий (`Progress`, `Control`, `Monitor`), контрольные точки выполнения, интеграция протокола инструментов MCP (Model Context Protocol).
3. **`Intelligent-Internet/ii-agent`** — персистентное управление сессиями, многошаговая память диалогов и песочница файлового пространства (`workspace`).
4. **`AFK-surf/open-agent`** — открытая альтернатива Claude Agent SDK / Manus с поддержкой совместной работы агентов и автоматизации устройств.
5. **`linuxhsj/openclaw-zero-token`** — универсальный шлюз нейросетей без токенов API: поддержка Claude, ChatGPT, Gemini, DeepSeek, Qwen, Kimi, Grok, а также локальных LLM (Ollama / vLLM / llama.cpp).
6. **`WhiskeyCoder/Qwen3-Audiobook-Converter`** — конвейер создания аудиокниг: парсинг PDF, EPUB, DOCX, TXT, интеллектуальный чанкинг предложений, разделение речи на рассказчика и реплики персонажей (многоголосая озвучка), кэширование и сборка итогового файла.
7. **`ServeurpersoCom/qwentts.cpp`** — высокопроизводительный C++ движок на базе GGML для локального низколатентного инференса Qwen3-TTS (CPU/CUDA/Metal/Vulkan), поддержка квантованных моделей (Q4_K_M, Q8_0) и потокового аудио.
8. **`filliptm/ComfyUI-FL-Qwen3TTS`** — готовый пакет пользовательских нод (`custom_nodes`) для ComfyUI, 9 предустановленных дикторов (Ryan, Serena, Vivian, Uncle Fu и др.), клонирование голоса по сэмплу, дизайн голоса по текстовому промпту и экспорт JSON-воркфлоу.
9. **`awesome-android-root/awesome-android-root`** — база знаний и каталог из 600+ проверенных root-приложений, модулей Magisk, KernelSU, APatch, LSPosed, руководств по разблокировке и скриптов оптимизации системы.

### ➕ Дополненные ключевые репозитории:

10. **`openatx/adbutils`** — чистый Python-клиент для взаимодействия с Android через встроенный ADB (USB и сеть Wi-Fi `adb connect ip:port`) без необходимости ставить внешние системные пакеты.
11. **`browser-use/browser-use`** — передовой фреймворк для взаимодействия автономного агента с веб-сайтами (DOM-дерево, клики, скролл, скриншоты).
12. **`modelcontextprotocol/python-sdk`** — стандарт Model Context Protocol (MCP) для динамического подключения инструментов.
13. **`SYSTRAN/faster-whisper` & `openai/whisper`** — быстрое локальное распознавание речи (STT) для двустороннего дуплексного голосового общения с агентом.
14. **`QwenLM/Qwen3-TTS`** — базовая архитектура 12-герцового аудиотокенизатора и акустического кодека от Alibaba.
15. **`py-pdf/pypdf`** — парсинг электронных книг и PDF-документов для конвертера аудиокниг.

---

## 🚀 Архитектура системы

```
                              +-------------------------------------------+
                              |         OmniNexus Web Studio UI           |
                              | (Tailwind + Canvas Waveform + Terminal)   |
                              +---------------------+---------------------+
                                                    |
                                      WebSocket / REST API (8000)
                                                    |
                                                    v
+---------------------------------------------------------------------------------------------------------+
|                                           FastAPI Application                                           |
+---------------------+---------------------+---------------------+---------------------+-----------------+
|  🤖 Agent Core      |  🎙️ Qwen3-TTS Engine |  📱 Android Suite   |  ⚡ OpenClaw Gateway |  🧩 ComfyUI Hub |
| - OpenManus ReAct   | - 24kHz Synth       | - Pure Python ADB   | - Zero-Token Bridge | - Node Pack     |
| - KODE 3 Channels   | - Voice Cloning     | - KernelSU / Magisk | - Multi-Provider    | - Workflow JSON |
| - II-Agent Memory   | - Voice Design      | - Live Mirror & Tap |   (Qwen, DeepSeek,  | - MCP Client    |
| - Tools (Bash, FS,  | - WhiskeyCoder      | - Debloater         |    Claude, GPT)     |                 |
|   Web, Python REPL) |   Audiobook Pipeline| - 600+ Root Catalog | - Local Ollama/vLLM |                 |
+---------------------+---------------------+---------------------+---------------------+-----------------+
```

---

## 🛠️ Основные модули и возможности

### 1. 🤖 Автономный агент (ReAct Workspace)
- **OpenManus ReAct Flow**: автономное разбиение задач на шаги, исполнение инструментов, оценка результата и самокоррекция.
- **KODE SDK 3-Channel Event Bus**: отдельные потоки данных в реальном времени:
  - `ProgressChannel`: ход выполнения шагов, промежуточные рассуждения;
  - `ControlChannel`: пауза, продолжение, подтверждение действий человеком;
  - `MonitorChannel`: задержка, метрики, ошибки и мониторинг памяти.
- **Инструменты агента**:
  - `bash`: запуск терминальных команд с таймаутом;
  - `file_operator`: чтение, запись, замена строк, поиск grep в файловой песочнице;
  - `web_search` & `fetch_page`: многопоточный поиск в сети и парсинг контента;
  - `python_execute`: запуск Python скриптов;
  - `synthesize_speech`: синтез аудиосообщений через Qwen3-TTS;
  - `android_device`: выполнение действий на телефоне (клики, свайпы, скриншоты, root-команды);
  - `mcp_connector`: интеграция инструментов по стандарту MCP.

### 2. 🎙️ Голосовая студия Qwen3-TTS & Конвертер аудиокниг
- **Высококачественный синтез (24 кГц)**: генерация естественного звука с формантным моделированием, модуляцией высоты тона и правильными паузами между фразами.
- **9 предустановленных дикторов**: Ryan (английский нарратор), Serena (нежный женский), Vivian (яркий женский), Aiden (глубокий мужской), Dylan (пекинский диалект), Eric (сычуаньский диалект), Uncle Fu (зрелый мужской), Ono Anna (японский), Sohee (корейский), Alex_RU и Elena_RU (русские голоса).
- **Клонирование голоса (Zero-Shot Voice Cloning)**: извлечение спектрального акустического профиля из сэмпла 5–15 секунд (WAV/MP3).
- **Дизайн голоса (Voice Design)**: генерация тембра по текстовому описанию (*«Глубокий бархатный мужской баритон со спокойным темпом»*).
- **Конвертер аудиокниг (WhiskeyCoder Pipeline)**:
  - Поддержка PDF, EPUB, DOCX, TXT.
  - Драматизация: автоматическое разделение текста на реплики персонажей и слова автора с назначением разных дикторов!
  - Пакетная конвертация, индикатор прогресса и объединение в итоговый WAV/MP3 файл.
- **Поддержка C++ GGML (`qwentts.cpp`)**: интеграция высокоскоростного нативного бинарника с авто-детекцией.

### 3. 💬 Двусторонний голосовой агент (Full-Duplex Voice)
- Общение голосом: запись через микрофон (Web Audio API) -> транскрибация -> рассуждение агента -> голосовой ответ диктором Qwen3-TTS с отображением спектрограммы.

### 4. 📱 Android Commander (awesome-android-root + ADB Bridge)
- **Подключение**: физический USB или беспроводной Wi-Fi (`adb connect <ip>:<port>`).
- **Виртуальная песочница**: встроенный симулятор Google Pixel 9 Pro (Android 15 / KernelSU root) для тестирования автоматизации без физического смартфона.
- **Интерактивное зеркало экрана**: живой скриншот с кликабельным тапом по координатам, свайпом и кнопками D-Pad (Home, Back, Recents, Power, Vol+, Vol-).
- **Root Shell Terminal**: прямое исполнение суперпользовательских команд (`su -c`).
- **Менеджер деблоатинга**: отключение предустановленных приложений и шпионского ПО производителя (`pm disable-user --user 0`).
- **Каталог Awesome Android Root**: встроенный полнотекстовый поиск по 600+ модулям (AdAway, Magisk, KernelSU, LSPosed, Viper4Android, инструкциям по рутированию).

### 5. ⚡ Мульти-модельный шлюз OpenClaw
- **Zero-Token Web Gateway**: использование передовых моделей (ChatGPT, Claude, DeepSeek, Qwen, Gemini, Kimi, Grok) через сессионный веб-мост без необходимости платных API-ключей.
- **BYOK / Подключение провайдеров**: прямое подключение ключей OpenAI, DeepSeek, Anthropic, Google, Groq, OpenRouter.
- **Локальные модели**: прямая интеграция с Ollama (`http://localhost:11434`), vLLM (`http://localhost:8001`) и llama.cpp.

### 6. 🧩 ComfyUI & MCP Hub
- Готовый модуль `comfyui_custom_nodes/ComfyUI-FL-Qwen3TTS`, который можно напрямую положить в папку `ComfyUI/custom_nodes/`.
- Экспорт готовых JSON воркфлоу для ComfyUI в 1 клик.

---

## ⚡ Быстрый старт

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Запуск сервера
```bash
./run.sh
# или
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Откройте в браузере: **`http://localhost:8000`**

---

## 🧪 Запуск тестов

Проект снабжен полным набором модульных и интеграционных тестов:

```bash
# Запуск полного набора тестов компонентов и агента
python3 -m unittest tests/test_all.py

# Запуск тестов HTTP API эндпоинтов FastAPI
python3 -m unittest tests/test_api.py
```

---

## 📁 Структура проекта

```
/home/user/New/
├── app/
│   ├── config.py                   # Центральные настройки приложения
│   ├── main.py                     # FastAPI сервер, REST эндпоинты, WebSockets
│   ├── agent/                      # Модуль агента (OpenManus + KODE + II-Agent)
│   │   ├── channels.py             # 3-канальная шина событий Kode SDK
│   │   ├── manus_core.py           # ReAct цикл планирования и исполнения
│   │   ├── memory.py               # Память сессий и контекст диалога
│   │   └── voice_agent.py          # Дуплексный голосовой агент
│   ├── tools/                      # Реестр инструментов агента
│   │   ├── base.py                 # Базовый класс и схемы JSON Schema
│   │   ├── terminal.py             # Выполнение bash/терминала
│   │   ├── workspace_fs.py         # Файловые операции в песочнице
│   │   ├── web_intelligence.py     # Поиск в сети и скрапер сайтов
│   │   ├── python_sandbox.py       # Запуск Python кода
│   │   ├── tts_tool.py             # Инструмент синтеза речи
│   │   ├── android_tool.py         # Инструмент управления Android
│   │   └── mcp_client.py           # Коннектор MCP инструментов
│   ├── audio/                      # Голосовая студия Qwen3-TTS
│   │   ├── voices.py               # Дикторы, профили, Voice Design
│   │   ├── synthesis.py            # 24 кГц акустический синтезатор
│   │   ├── engine.py               # Оркестратор TTS (Python + qwentts.cpp + API)
│   │   ├── audiobook.py            # Конвертер PDF/EPUB/DOCX/TXT в аудиокниги
│   │   └── comfyui_integration.py  # Экспортер воркфлоу ComfyUI
│   ├── android/                    # Android Commander & Root Suite
│   │   ├── bridge.py               # ADB подключение (USB / TCP)
│   │   ├── controller.py           # Тапы, свайпы, скриншоты, управление приложениями
│   │   ├── virtual_device.py       # Симулятор Pixel 9 Pro с KernelSU
│   │   └── knowledge_base.py       # База знаний awesome-android-root (600+ записей)
│   ├── gateway/                    # Шлюз нейросетей OpenClaw
│   │   ├── catalog.py              # Каталог 50+ моделей
│   │   ├── zero_token.py           # Веб-сессии без токенов
│   │   ├── providers.py            # Клиенты OpenAI, Anthropic, Ollama, DeepSeek
│   │   └── router.py               # Маршрутизатор с авто-отказоустойчивостью
│   └── web/
│       ├── static/                 # CSS (Tailwind Dark Glassmorphism) и JS
│       └── templates/              # HTML веб-интерфейс
├── comfyui_custom_nodes/           # Пакет для папки ComfyUI/custom_nodes/
├── native/qwentts/                 # C++ GGML биндинги qwentts.cpp
├── data/
│   ├── audiobooks/                 # Каталог созданных аудиокниг
│   ├── samples/                    # Примеры текстов и сэмплов
│   └── workspace/                  # Рабочая изолированная директория агента
├── docs/                           # Подробная документация
│   ├── ARCHITECTURE.md             # Детальная архитектурная схема
│   ├── REPOSITORIES_INTEGRATION.md # Детали интеграции 15 репозиториев
│   ├── API_REFERENCE.md            # Спецификация REST и WebSocket API
│   └── ANDROID_ROOT_GUIDE.md       # Руководство по Android и Root
├── tests/                          # Набор тестов
├── requirements.txt
├── pyproject.toml
└── run.sh                          # Скрипт запуска
```

---

<a name="english-description"></a>
## 🇬🇧 English Description

**OmniNexus Studio** is an all-in-one operating platform unifying:
- **Autonomous Multi-Agent ReAct Engine** (`OpenManus` + `kode-agent-sdk` + `ii-agent` + `open-agent`) with 3-channel event streaming (`Progress`, `Control`, `Monitor`).
- **Qwen3-TTS Voice & Audiobook Studio** (`WhiskeyCoder/Qwen3-Audiobook-Converter` + `ServeurpersoCom/qwentts.cpp` + `filliptm/ComfyUI-FL-Qwen3TTS`) supporting 24kHz audio, 9 predefined speakers, zero-shot voice cloning, prompt-based voice design, and multi-speaker dramatized document conversion (PDF/EPUB/DOCX/TXT).
- **Universal Model Gateway** (`linuxhsj/openclaw-zero-token`) with Zero-Token reverse-proxy web bridges and BYOK fallback across Claude, GPT-4o, DeepSeek, Qwen, Gemini, Kimi, and local Ollama.
- **Android Device Commander** (`awesome-android-root` + `adbutils`) with interactive screen mirroring, click-to-tap, swipe, key controls, package debloater, root shell terminal (`su -c`), and a searchable 600+ root apps & modules directory.
- **Bidirectional Full-Duplex Voice Dialogue** with real-time speech input, agent reasoning, and audible voice responses.

### License
MIT License.
