#!/usr/bin/env bash

echo "WARNING: This will reset your working directory!"
echo "Please make sure all your changes are committed and merged into master."
read -p "Are you sure you want to continue? " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "Preparing to build..."
    {
        rm -r build & rm -r dist
        git reset --hard
        git checkout master
        git pull --ff
    } &> /dev/null
    echo "Building new release..."
    {
        python setup.py bdist_wheel
        WHEEL="$(ls -t1 dist/ | head -n 1)"
    } &> /dev/null
    echo "New release created:" $WHEEL
    read -p "Would you like to upload to PyPi? " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]
    then
        {
            twine upload dist/$WHEEL
        } &> /dev/null
        echo "Upload complete."
    fi
    {
        rm -r build & rm -r dist
    } &> /dev/null
fi
