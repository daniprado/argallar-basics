#!/bin/bash

LBIN_PATH="${HOME}/.local/bin"
CURR_PATH=$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source ${CURR_PATH}/_files/common.sh

if [[ :${PATH}: != *:"${LBIN_PATH}":* ]]; then
  export PATH="${LBIN_PATH}:${PATH}"
  LBIN_NOT_IN_PATH="True"
fi

pipx_install "${CURR_PATH}/_files/argallar-basics-py"

if [[ ! -z ${LBIN_NOT_IN_PATH} ]]; then
  echo "--- Execute as .local/bin is not in PATH ---"
  echo "export PATH=\"\${HOME}/.local/bin:\${PATH}\""
  echo "--------------------------------------------"
fi

exit 0
