# Do for Vim

## Run asynchronous shell commands and display the output

The aim of this plugin is to provide a quick and simple way of running shell commands in the background, and displaying the results (output, exit status, etc) in a Vim buffer after the command has finished. That means you can run a command, carry on working in Vim, and then have the output shown to you when it's available.

It works nicely for both short- and long-running processes, and the great thing is that you don't have to swap between a terminal and Vim to run commands or see their output.

## Quick Start

After installing (see below) you're given the `:Do` vim command, which allows you to run any shell command:

```vim
:Do echo "hi"
:Do rake
:Do find /
```

Oops, that last command is gonna take a while...

But don't worry, it's asynchronous! The output will pop up in a new vim buffer when the command finishes running.

## Install

**Requires Vim compiled with Python 2.4+ support**

### Classic

Clone or download a tarball of the plugin and move its content in your
`~/.vim/` directory.

Your `~/.vim/plugin/` directory should now contain vdebug.vim and a directory
called "python".

### Using git and Pathogen

Clone this repository in your `~/.vim/bundle` directory

### Using vundle

Add this to your `~/.vimrc` file:

```vim
Bundle 'joonty/vim-do.git'
```

Then, from the command line, run:

```bash
vim +BundleInstall +qall
```

## Configuration

Zilch, currently. (FIXME)

## How does it work?

Actual, genuine, bona-fide magic. (FIXME)

## License

This is released under the MIT license.
