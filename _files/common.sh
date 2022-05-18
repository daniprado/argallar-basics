#!/bin/bash

export AG_DOTFILES="${AG_SRC:-$HOME/dotfiles}"

[[ "${XDG_CONFIG_HOME}" != "${HOME}"* ]] && export XDG_CONFIG_HOME="${HOME}/.config"
export AG_CONFIG="${XDG_CONFIG_HOME}"
[[ "${XDG_CACHE_HOME}" != "${HOME}"* ]] && export XDG_CACHE_HOME="${HOME}/.cache"
export AG_CACHE="${XDG_CACHE_HOME}"
[[ "${XDG_RUNTIME_DIR}" != "${HOME}"* ]] && export XDG_RUNTIME_DIR="/tmp"
export AG_RUNTIME="${XDG_RUNTIME_DIR}"

export AG_TEMP="${HOME}/tmp"
export AG_SHARE="${HOME}/.local/share"
export AG_BIN="${HOME}/.local/bin"
export AG_SSH="${HOME}/.ssh"

[[ -z ${AG_STRICT} ]] || set -e

is_tbi () {
  local cmd=$1
  if [[ ! -z "${AG_INSTALL}" ]]; then
    if ! type "${cmd}" >/dev/null; then
      return 1
    fi
  fi
  return 0
}
export -f is_tbi

exe () {
  local cmd=$1
  if [[ -z "${AG_FAKE}" ]]; then
    eval ${cmd}
  fi
  echo "${cmd}"
}
export -f exe

install () {
  local cmd=$1
  local instcmd=$2
  is_tbi "${cmd}" || exe "${instcmd}"
}

clone_repo () {
  local repo_url=$1
  local clone_path=$2
  local params=$3

  if [[ -d "${clone_path}" ]]; then
    exe "(cd ${clone_path}; git pull)"
    return 1 #Found!
  else
    exe "git clone ${params} ${repo_url} ${clone_path}"
  fi

  return 0
}
export -f clone_repo

create_folders () {
  local folders=("$@")

  for folder in "${folders[@]}"; do
    exe "mkdir --parents ${folder}"
  done
}
export -f create_folders

pip_install () {
  local packages=("$@")

  for pkg in "${packages[@]}"; do
    exe "(cd ${HOME}; pip install --user ${pkg})"
  done
}
export -f pip_install

pipx_install () {
  local packages=("$@")

  for pkg in "${packages[@]}"; do
    exe "(cd ${HOME}; pipx install --force ${pkg})"
  done
}
export -f pipx_install

pkg_install () {
  local cmd="$1"
  local pacman_pkg=$([[ ! -z "$2" ]] && echo "$2" || echo "${cmd}")
  local apt_pkg=$([[ ! -z "$3" ]] && echo "$3" || echo "${pacman_pkg}")
  local yum_pkg=$([[ ! -z "$4" ]] && echo "$4" || echo "${apt_pkg}")

  is_tbi "${cmd}"
  if [[ "$?" -eq "1" ]]; then
    if type "pacman" >/dev/null && [[ "-" != "${pacman_pkg}" ]]; then
      exe "sudo pacman -S ${pacman_pkg}"
    elif type "apt" >/dev/null && [[ "-" != "${apt_pkg}" ]]; then
      exe "sudo apt install -y ${apt_pkg}"
    elif type "yum" >/dev/null && [[ "-" != "${yum_pkg}" ]]; then
      exe "sudo yum install ${yum_pkg}"
    fi
  fi
}
export -f pkg_install

create_link () {
  local orig="$1"
  local dest="$2"

  exe "ln -s ${orig} ${dest}"
}
export -f create_link

remove () {
  local locations=("$@")
  for loc in "${locations[@]}"; do
    exe "rm -rf ${loc}"
  done
}
export -f remove
