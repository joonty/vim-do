" Vim syntax file
" Language: Vim Debugger Watch Window
" Maintainer: Jon Cairns
" Latest Revision: 2 August 2012

if exists("b:current_syntax")
  finish
endif

syn region doCommandHeader start=+^=+ end=+=$+
syn match doCommandTitle '\zs\[\(command\|status\|time\|pid\)\]\ze'
syn region doCommandStderr start=+^`+ end=+`$+

hi def link doCommandHeader Type
hi def link doCommandTitle Title
hi def link doCommandStderr Error
