#!/bin/bash
# ==============================================================================
# Filename: setup_project.sh
# About: initialize project (test with macOS, Python 3.12.7)
# ==============================================================================

# ==============================================================================
# User's basic variables
# ==============================================================================
PROJECT_NAME="HouseWatch"
PROJECT_NAME_LOWER=$(echo "$PROJECT_NAME" | tr '[:upper:]' '[:lower:]')
ENV_NAME="${PROJECT_NAME_LOWER}-env"
PYTHON_VERSION="3.12.7"

echo "Project name:    $PROJECT_NAME"
echo "Env name:        $ENV_NAME"
echo "Python version:  $PYTHON_VERSION"

# ==============================================================================
# Project structure
#   - this is usually managed using git repository
# ==============================================================================
# git clone ....
# cd ${PROJECT_NAME}
echo "Build project ${PROJECT_NAME} in its own base folder: ${PROJECT_NAME}"
# Check basename (full path looks like ~/Development/project/${PROJECT_NAME})
CURRENT_DIR_NAME=$(basename "$(pwd)")
if [ "$CURRENT_DIR_NAME" = "$PROJECT_NAME" ]; then
    echo "✅ Directory name matches project name: $PROJECT_NAME"
else
    echo "❌ Directory name mismatch!"
    echo "  Current directory: $CURRENT_DIR_NAME"
    echo "  Expected project:  $PROJECT_NAME"
    return
fi

# ==============================================================================
# Conda virtual environment
# ==============================================================================
# Check if conda is installed
if ! command -v conda &>/dev/null; then
    echo "❌ conda command not found. Please install Miniconda or Anaconda first."
    return
fi

# Check if conda virtural environment exists
if conda info --envs | grep -qE "^${ENV_NAME}[[:space:]]"; then
  echo "✅ Environment '$ENV_NAME' already exists. Activating..."
else
  echo "🆕 Environment '$ENV_NAME' not found. Creating..."
  conda create -y -n "$ENV_NAME" python="$PYTHON_VERSION"
  # usually the env folder can be found at: ~/miniconda3/envs/${ENV_NAME}
fi


conda activate "$ENV_NAME"
echo "✅ Environment '$ENV_NAME' is now active."

# set up python
unset PYTHONPATH
export PYTHONPATH="$(pwd)/src"
echo "✅ PYTHONPATH set to $PYTHONPATH"

# install a package
echo -e "To install a package, use \n  $ conda install -y numpy"

# export installed packages
echo -e "To export installed packages, use \n $ conda list --export > requirements.txt"

# export current active environment
echo -e "To export the active environment, use \n  $ conda env export > environment.yml"

# rebuid the same environment
echo -e "To rebuild the same environment, use \n  $ conda env create -f environment.yml"

# deactivate
echo -e "To deactivate an active environment, use \n  $ conda deactivate"
