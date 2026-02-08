# 🔒 Secure Messenger

A secure, end-to-end encrypted messaging application with a modern GUI built using Python, CustomTkinter, and cryptography libraries.

## ✨ Features

- **🔐 Secure Communication**: End-to-end encryption for all messages
- **👥 User Management**: Registration, login, and authentication system
- **💬 Multiple Chat Modes**: 
  - Direct messaging between users
  - Public chat rooms
- **📝 Persistent Storage**: SQLite database for message history and user data
- **🎨 Modern GUI**: Clean, dark-themed interface using CustomTkinter
- **🔄 Real-time Updates**: Live message synchronization across clients
- **📊 High Test Coverage**: 90% code coverage with comprehensive unit tests

## 🏗️ Project Structure

```
FMI_Python/
├── src/
│   ├── client/
│   │   ├── gui.py           # CustomTkinter GUI implementation
│   │   └── network.py       # Client-side network communication
│   ├── server/
│   │   ├── server_main.py   # Main server logic and connection handling
│   │   └── database.py      # Database operations (SQLite)
│   └── common/
│       ├── protocol.py      # Network protocol (JSON-based)
│       └── crypto_utils.py  # Encryption utilities
├── tests/                   # Unit tests with pytest
├── assets/                  # Image resources for GUI
└── pyproject.toml          # Project configuration
```

## 🚀 Quick Start with UV

This project uses [uv](https://github.com/astral-sh/uv) - an extremely fast Python package installer and resolver. It's 10-100x faster than pip!

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Installing UV

**Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd FMI_Python
   ```

2. **Install everything with one command**
   ```bash
   uv sync
   ```

**That's it!** 🎉 This single command will:
- Create a virtual environment (`.venv`)
- Install all dependencies from the lockfile (`uv.lock`)
- Install the project in editable mode
- Ensure everyone has the exact same dependency versions

> **Note**: You don't need to manually activate the virtual environment. Use `uv run` to execute commands (see below).

## 📚 Common UV Commands

### Daily Development
```powershell
uv run pytest                              # Run tests with coverage
uv run python -m src.server.server_main    # Start server
uv run python -m src.client.gui            # Start client GUI
uv run mypy src                            # Type checking
uv run pylint src                          # Code linting
```

### Managing Dependencies
```powershell
# Add a new dependency:
uv add package-name        # Adds to pyproject.toml and updates lockfile

# Remove a dependency:
uv remove package-name     # Removes from pyproject.toml and updates lockfile

# Update dependencies to latest compatible versions:
uv lock --upgrade          # Update lockfile
uv sync                    # Install updated dependencies

# Sync after pulling changes (if lockfile changed):
uv sync
```

## 🎮 Usage

### Running the Server

```bash
uv run python -m src.server.server_main
```

The server will start on `127.0.0.1:5050` by default.

### Running the Client

```bash
uv run python -m src.client.gui
```

This launches the GUI application where you can:
1. Register a new account or login
2. Start chatting with other users
3. Create or join public rooms

## 🧪 Testing

### Run All Tests

```bash
uv run pytest
```

### Run Tests with Detailed Coverage Report

```bash
uv run pytest --cov=src --cov-report=term-missing
```

This shows exactly which lines are missing coverage.

### Generate HTML Coverage Report

```bash
uv run pytest --cov=src --cov-report=html
```

Then open `htmlcov/index.html` in your browser for an interactive coverage report.

### Current Test Coverage

The project maintains **90% test coverage** across all modules:
- `protocol.py`: 100%
- `database.py`: 100%
- `crypto_utils.py`: 94%
- `gui.py`: 91%
- `network.py`: 87%
- `server_main.py`: 78%

## 🛠️ Development Tools

### Type Checking with MyPy

```bash
uv run mypy src
```

### Linting with Pylint

```bash
uv run pylint src
```

### Running All Quality Checks

```bash
uv run pytest && uv run mypy src && uv run pylint src
```

## 📦 Dependencies

- **customtkinter**: Modern GUI framework
- **cryptography**: Encryption and security
- **Pillow**: Image processing for GUI assets
- **pytest & pytest-cov**: Testing and coverage
- **mypy**: Static type checking
- **pylint**: Code quality and style checking
- **requests**: HTTP client library
- **python-dotenv**: Environment variable management

All dependencies are managed through `pyproject.toml` and installed automatically via `uv`.

## 🔧 Configuration

The project uses `pyproject.toml` for all configuration:

- **Build system**: setuptools
- **Python version**: 3.10+
- **Test settings**: pytest with coverage enabled by default
- **Type checking**: mypy with strict settings
- **Linting**: pylint with 120 character line limit

## 📝 Environment Variables

Create a `.env` file in the project root for custom configuration (optional):

```env
HOST=127.0.0.1
PORT=5050
```

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Run tests: `uv run pytest`
4. Run type checker: `uv run mypy src`
5. Run linter: `uv run pylint src`
6. Ensure all checks pass before submitting

## 🔒 Security Notes

- Server keys are stored in `server.key` (excluded from git)
- Database is stored in `data/data.db` (excluded from git)
- Never commit `.env` files or private keys

## 📄 License

Course Project - Educational Use

## 🙋 Support

For issues or questions about setup:
1. Ensure Python 3.10+ is installed: `python --version`
2. Verify `uv` is properly installed: `uv --version`
3. Try re-syncing: `uv sync`
4. Check installed packages: `uv pip list`

---
