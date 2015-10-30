" Vim syntax file
" Language: Vim Debugger Watch Window
" Maintainer: Jon Cairns
" Latest Revision: 2 August 2012

if exists("b:current_syntax")
  finish
endif

syn region doCommandWindowHeader start=+^=+ end=+=$+
syn match doCommandWindowDivider '|'
syn match doCommandWindowTitle '[A-Z]\{2,}'
syn match doCommandWindowPid '\s\d\{5,}\s'


hi def link doCommandWindowHeader Type
hi def link doCommandWindowDivider Type
hi def link doCommandWindowTitle Title
hi def link doCommandWindowPid Number
