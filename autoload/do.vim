" Exit when already loaded (or "compatible" mode set)
if exists("g:do_loaded") || &cp
    finish
endif

" Vars used by this script, don't change
let g:do_loaded = 1
let s:existing_update_time = &updatetime
let s:previous_command = ""

" Configuration vars
let s:do_check_interval = 500
let s:do_new_buffer_command_prefix = ""
let s:do_new_buffer_size = ""
let s:do_refresh_key = "<C-L>"
let s:do_update_time = 500

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
" Execute a shell command asynchronously, from the current visually selected text.
"
" See do#Execute() for more information.
"
function! do#ExecuteSelection()
    let l:command = s:getVisualSelection()
    call do#Execute(l:command)
endfunction

""
" Enable the file logger for debugging purposes.
"
" @param string file_path The path to the file to write log information
"
function! do#EnableLogger(file_path)
python <<_EOF_
do_async.enable_logger(vim.eval("a:file_path"))
_EOF_
endfunction

""
" Show or hide the command window.
"
" The command window details currently running and finished processes.
"
function! do#ToggleCommandWindow()
    python do_async.toggle_command_window()
endfunction

""
" A callback for when the command window is closed.
"
" Executed automatically via an autocommand.
"
function! do#MarkCommandWindowAsClosed()
    python do_async.mark_command_window_as_closed()
endfunction

""
" A callback for when the process window is closed.
"
" Executed automatically via an autocommand.
"
function! do#MarkProcessWindowAsClosed()
    python do_async.mark_process_window_as_closed()
endfunction

""
" Trigger selection of a process in the command window.
"
function! do#ShowProcessFromCommandWindow()
    python do_async.show_process_from_command_window()
endfunction

""
" Do nothing.
"
" Used in do#AssignAutocommands()
"
function! do#nop()
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
    execute "nnoremap <silent> " . do#get("do_refresh_key") . " :call do#nop()<CR>"
    execute "inoremap <silent> " . do#get("do_refresh_key") . ' <C-O>:call do#nop()<CR>'
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

" Thanks to http://stackoverflow.com/a/6271254/1087866
function! s:getVisualSelection()
  " Why is this not a built-in Vim script function?!
  let [lnum1, col1] = getpos("'<")[1:2]
  let [lnum2, col2] = getpos("'>")[1:2]
  let lines = getline(lnum1, lnum2)
  let lines[-1] = lines[-1][: col2 - (&selection == 'inclusive' ? 1 : 2)]
  let lines[0] = lines[0][col1 - 1:]
  return join(lines, "\n")
endfunction

" Initialize do
python do_async = Do()
autocmd VimLeavePre * python do_async.stop()
