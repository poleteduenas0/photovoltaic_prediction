#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# setup.sh - Project setup script con UV
# -----------------------------------------------------------------------------
set -euo pipefail

PROJECT_NAME="$(basename "$(pwd)")"
PYTHON_MIN=3.11

echo "[setup] Project: $PROJECT_NAME"

# Verificar que UV está instalado
if ! command -v uv >/dev/null 2>&1; then
  echo "UV no está instalado. Instalando UV..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.cargo/bin:$PATH"
fi

echo "[setup] UV version: $(uv --version)"

# Crear venv con UV si no existe
if [ ! -d ".venv" ]; then
  echo "[setup] Creando entorno virtual con UV..."
  uv venv --python 3.11
fi

# Activar el entorno
if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
elif [ -f ".venv/Scripts/activate" ]; then
  source .venv/Scripts/activate
fi

echo "[setup] Instalando dependencias..."
# Sincronizar todas las dependencias definidas en pyproject.toml
uv sync

# Instalar el proyecto en modo editable
echo "[setup] Instalando proyecto en modo editable..."
uv pip install -e .

echo ""
echo "[setup] ✅ Instalación completada"
echo "[setup] Activar entorno: source .venv/bin/activate (Linux/Mac)"
echo "[setup]                  .venv\\Scripts\\activate (Windows)"
echo "[setup] Ejecutar tests: pytest"
echo "[setup] Ver dependencias: uv pip list"