#!/bin/bash
# This bash file is to be sourced at login and must have .sh extension

# Excerpt from:
# https://github.com/travis-ci/travis-build/blob/d5760f7925d62fcad1737c02dc6486387aa8b432/lib/travis/build/templates/header.sh

ANSI_RED="\033[31;1m"
ANSI_GREEN="\033[32;1m"
ANSI_YELLOW="\033[33;1m"
ANSI_RESET="\033[0m"
ANSI_CLEAR="\033[0K"

travis_retry() {
  local result=0
  local count=1
  while [ $count -le 3 ]; do
    [ $result -ne 0 ] && {
      echo -e "\n${ANSI_RED}The command \"$*\" failed. Retrying, $count of 3.${ANSI_RESET}\n" >&2
    }
    "$@" && { result=0 && break; } || result=$?
    count=$(($count + 1))
    sleep 1
  done
  [ $count -gt 3 ] && {
    echo -e "\n${ANSI_RED}The command \"$*\" failed 3 times.${ANSI_RESET}\n" >&2
  }
  return $result
}
