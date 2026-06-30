# Ansys Material Database

Ansys thermal simulation material database management tool with AI-powered property extraction.

## Features

- **Material Library** - Browse, search, edit, and manage materials with full property support
- **Document Import** - Import supplier PDF manuals and images as knowledge base documents
- **AI Property Extraction** - Use multimodal LLM to automatically extract material properties (density, thermal conductivity, specific heat, thermal expansion, Poisson's ratio) from documents
- **XML Export** - Export materials to Ansys 2021 R1 compatible Engineering Data XML format
- **XML Viewer** - Import and view existing Ansys XML material libraries
- **Internationalization** - Full Chinese/English UI with one-click language switching
- **OpenAI-compatible LLM** - Connect to any OpenAI API-compatible model (e.g., mimo-v2.5)

## Requirements

- Python 3.10+
- Ansys Workbench 2021 R1 (for XML import)

## Installation

`ash
git clone https://github.com/lktx/ansys-material-db.git
cd ansys-material-db
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -e .
`

## Usage

`ash
python -m ansys_material_db.main
`

### Standalone Executable

Download AnsysMaterialDB.exe from [Releases](https://github.com/lktx/ansys-material-db/releases) and double-click to run.

### LLM Configuration

1. Open **Settings** in the app
2. Enter your API Base URL, API Key, and Model name
3. Click **Test Connection** to verify

## Project Structure

`
src/ansys_material_db/
├── app.py                # Application setup and backend wiring
├── main.py               # Entry point
├── i18n.py               # Internationalization (Chinese/English)
├── config/
│   └── settings.py       # App settings
├── core/
│   ├── document_parser.py      # PDF/image text extraction
│   ├── knowledge_base.py       # Document import orchestration
│   ├── property_extractor.py   # LLM-based property extraction
│   ├── qa_engine.py            # Q&A engine
│   └── xml_generator.py        # Ansys XML generation
├── data/
│   ├── database.py             # SQLite manager
│   ├── embeddings.py           # Text embedding service
│   └── llm_client.py           # OpenAI-compatible LLM client
├── gui/
│   ├── main_window.py          # Main window with toolbox navigation
│   ├── material_browser.py     # Material tree view with search/filter
│   ├── property_editor.py      # Material property editing
│   ├── document_manager.py     # Document list and extraction
│   ├── export_page.py          # XML export interface
│   ├── xml_viewer_page.py      # XML file viewer
│   ├── settings_page.py        # LLM and UI settings
│   └── styles.py               # Ansys-inspired dark theme
└── models/
    ├── material.py             # Material and MaterialProperty
    └── document.py             # Document and TextChunk
`

## License

MIT