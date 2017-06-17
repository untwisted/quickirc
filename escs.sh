##############################################################################
# push, quickirc, github.
cd ~/projects/quickirc-code
git status
git add *
git commit -a
git push 
##############################################################################
# create the develop branch, quickirc.
git branch -a
git checkout -b development
git push --set-upstream origin development
##############################################################################
# merge master into development, quickirc.
cd ~/projects/quickirc-code
git checkout development
git merge master
git push
##############################################################################
# merge development into master, quickirc.
cd ~/projects/quickirc-code
git checkout master
git merge development
git push
git checkout development
##############################################################################
# check diffs, quickirc.
cd ~/projects/quickirc-code
git diff
##############################################################################
# delete the development branch, quickirc.
git branch -d development
git push origin :development
git fetch -p 
##############################################################################
# undo, changes, quickirc, github.
cd ~/projects/quickirc-code
git checkout *
##############################################################################
# install, quickirc.
sudo bash -i
cd /home/tau/projects/quickirc-code
python2 setup.py install
rm -fr build
exit
##############################################################################
# build, quickirc, package, disutils.
cd /home/tau/projects/quickirc-code
python2.6 setup.py sdist 
rm -fr dist
rm MANIFEST
##############################################################################
# share, put, place, host, package, python, pip, application, quickirc.

cd ~/projects/quickirc-code
python2 setup.py sdist register upload
rm -fr dist
##############################################################################



