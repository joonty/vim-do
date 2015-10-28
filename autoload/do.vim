" Exit when already loaded (or "compatible" mode set)
if exists("g:do_loaded") || &cp
    finish
endif

" Vars used by this script
let g:do_loaded = 1
let s:existing_update_time = &updatetime
let s:previous_command = ""

" Configuration vars
let s:do_update_time = 1000
let s:do_new_buffer_prefix = ""
let s:do_new_buffer_size = ""

" Load Python script
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

" Initialize do
python do_async = Do()

""
" Fetch a scoped value of an option
"
" Determine a value of an option based on user configuration or pre-configured
" defaults. A user can configure an option by defining it as a buffer variable
" or as a global (buffer vars override globals). Default value can be provided
" by defining a script variable for the whole file or a function local (local
" vars override script vars). When all else fails, falls back the supplied
" default value,  if one is supplied.
"
" @param string option Scope-less name of the option
" @param mixed a:1 An option default value for the option
"
function! do#get(option, ...)
    for l:scope in ['b', 'g', 'l', 's']
        if exists(l:scope . ':' . a:option)
            return eval(l:scope . ':' . a:option)
        endif
    endfor

    if a:0 > 0
        return a:1
    endif

    call do#error('Invalid or undefined option: ' . a:option)
endfunction

""
" Show user an error message
"
" Pre-format supplied message as an Error and display it to the user. All
" messages are saved to message-history and are accessible via `:messages`.
"
" @param string message A message to be displayed to the user
"
function! do#error(message)
    echohl Error | echomsg a:message | echohl None
endfunction

""
" Execute the last command again.
"
" See do#Execute().
"
function! do#ExecuteAgain()
    if empty(s:previous_command)
        call do#error("You cannot execute the previous command when no previous command exists!")
    else
        call do#Execute(s:previous_command)
    endif
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
        call do#error("Supplied command is empty")
    else
        let s:previous_command = l:command
python <<_EOF_
do_async.execute(vim.eval("l:command"))
_EOF_
    endif
endfunction

""
" Show a window detailing the running and completed commands.
"
function! do#ShowCommands()

endfunction

""
" Assign auto commands that are used after a command has started execution.
"
" This combination of auto commands should cover most cases of the user being
" idle or using vim. The updatetime is set to that defined by the option
" g:do_update_time, which is typically more regular than the default.
"
" Autocommands are added in a group, for easy removal.
"
function! do#AssignAutocommands()
    augroup vim_do
        au CursorHold * python do_async.check()
        au CursorHoldI * python do_async.check()
        au CursorMoved * python do_async.check()
        au CursorMovedI * python do_async.check()
        au FocusGained * python do_async.check()
        au FocusLost * python do_async.check()
    augroup END
    let &updatetime=do#get("do_update_time")
endfunction

""
" Remove all autocommands set by do#AssignAutocommands().
"
" Also reset the updatetime to what it was before assigning the autocommands.
"
function! do#UnassignAutocommands()
    au! vim_do
    let &updatetime=s:existing_update_time
endfunction

" PRIVATE FUNCTIONS
" -----------------

" Strip whitespace from input strings.
"
" @param string input_string The string which requires whitespace stripping
"
function! Strip(input_string)
    return substitute(a:input_string, '^\s*\(.\{-}\)\s*$', '\1', '')
endfunction

