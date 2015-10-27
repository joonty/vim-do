" Exit when already loaded (or "compatible" mode set)
if exists("g:loaded_do") || &cp
    finish
endif
let g:loaded_do= 1

if filereadable($VIMRUNTIME."/plugin/python/do.py")
  pyfile $VIMRUNTIME/plugin/do.py
elseif filereadable($HOME."/.vim/plugin/python/do.py")
  pyfile $HOME/.vim/plugin/python/do.py
else
  " when we use pathogen for instance
  let $CUR_DIRECTORY=expand("<sfile>:p:h")

  if filereadable($CUR_DIRECTORY."/python/do.py")
    pyfile $CUR_DIRECTORY/python/do.py
  else
    call confirm('vdebug.vim: Unable to find do.py. Place it in either your home vim directory or in the Vim runtime directory.', 'OK')
  endif
endif

python do_async = CommandPool()

function! Strip(input_string)
    return substitute(a:input_string, '^\s*\(.\{-}\)\s*$', '\1', '')
endfunction

""
" Execute a shell command asynchronously.
"
" If a command string is supplied, this will be executed. If no argument (or
" an empty string) is supplied, it will default to using the command set by
" the vim setting "makeprg", which defaults to `make`.
"
" Any special file modifiers will get expanded, such as "%". This allows you
" to run commands like "test %", where "%" will be expanded to the current
" file name.
"
" @param string command (optional) The command to run, defaults to &makeprg
"
function! do#Execute(command)
    let l:command = a:command
    if empty(l:command)
        let l:command = &makeprg
    endif
    let l:command = Strip(join(map(split(l:command, '\ze[<%#]'), 'expand(v:val)'), ''))
    if empty(l:command)
        echohl Error | echo "Supplied comand is empty" | echohl Normal
    else
python <<_EOF_
do_async.execute(vim.eval("l:command"))
_EOF_
    endif
endfunction
