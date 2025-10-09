#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${1:-DLCv3-WebUI-test}"
PYTHON_VERSION="3.10"
CUDA_SPEC="nvidia/label/cuda-12.4.1::cuda-toolkit"
CONDA_CHANNELS=(
  "pytorch"
  "nvidia"
  "rapidsai"
  "https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/"
  "https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud//pytorch/"
  "conda-forge"
  "defaults"
)
PIP_INDEX_URL="https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple"

step_counter=1
step() {
  printf '\n[%02d] %s\n' "${step_counter}" "$1"
  step_counter=$((step_counter + 1))
}

die() {
  printf 'Error: %s\n' "$1" >&2
  exit 1
}

if ! command -v conda >/dev/null 2>&1; then
  die "conda is not available. Install Miniconda or Anaconda first."
fi

if ! command -v mamba >/dev/null 2>&1; then
  step "Installing mamba into the base environment"
  conda install -n base -c conda-forge mamba -y
fi

step "Loading conda shell integration"
eval "$(conda shell.bash hook)"

step "Configuring conda channels"
for channel in "${CONDA_CHANNELS[@]}"; do
  if ! conda config --show channels | grep -Fx "  - ${channel}" >/dev/null 2>&1; then
    conda config --add channels "${channel}"
  fi
done

step "Configuring pip index URL"
export PIP_INDEX_URL="${PIP_INDEX_URL}"

step "Creating or updating the ${ENV_NAME} environment"
if conda env list | awk '{print $1}' | grep -Fxq "${ENV_NAME}"; then
  printf 'Environment %s already exists; skipping creation.\n' "${ENV_NAME}"
else
  mamba create -n "${ENV_NAME}" "python=${PYTHON_VERSION}" -y
fi

step "Activating ${ENV_NAME}"
conda activate "${ENV_NAME}"

step "Installing CUDA toolkit ${CUDA_SPEC}"
mamba install "${CUDA_SPEC}" -y

step "Installing Torch stack via pip"
python -m pip install --upgrade pip
python -m pip install torch torchvision torchaudio

step "Installing pytables==3.8.0 from conda-forge"
mamba install -c conda-forge "pytables==3.8.0" -y

step "Uninstalling numpy to align with DeepLabCut requirements"
if python -m pip show numpy >/dev/null 2>&1; then
  python -m pip uninstall -y numpy
fi

step "Installing DeepLabCut release candidate"
python -m pip install "deeplabcut==3.0.0rc13"

step "Verifying DeepLabCut import"
python - <<'PYTHON'
import sys
try:
    import deeplabcut  # noqa: F401
except Exception as exc:  # pragma: no cover
    sys.exit(f"deeplabcut import failed: {exc}")
PYTHON

step "Installing UI dependencies"
python -m pip install streamlit GPUtil streamlit-authenticator ffmpeg

step "Completed environment setup"
echo "Activate it anytime with: conda activate ${ENV_NAME}"
