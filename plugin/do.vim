" Do: Run shell commands asynchronously and show the output in Vim
"
" Script Info  {{{
"=============================================================================
"    Copyright: Copyright (C) 2015 Jon Cairns
"      Licence:	The MIT Licence (see LICENCE file)
" Name Of File: do.vim
"  Description: Run shell commands asynchronously and show the output in Vim
"   Maintainer: Jon Cairns <jon at joncairns.com>
"      Version: 0.0.1
"        Usage: Use :help Do for information on how to configure and use
"               this script, or visit the Github page http://github.com/joonty/vim-do.
"
"=============================================================================
" }}}

if !has("python")
    finish
endif

command! -nargs=* Do call do#Execute(<q-args>)
command! -range DoThis call do#ExecuteSelection()
command! DoAgain call do#ExecuteAgain()
command! Doing call do#ToggleCommandWindow()
command! Done call do#ToggleCommandWindow()

" Looking for the rest? Check the autoload directory :D
