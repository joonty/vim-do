#!/bin/bash
version=`cat VERSION`
echo "Building vdebug version $version"
tar -cvzf vim-do-$version.tar.gz --exclude=build.sh  *
