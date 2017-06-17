##############################################################################
# push, qirc, github.
cd ~/projects/qirc-code
git status
git add *
git commit -a
git push 
##############################################################################
# create the develop branch, qirc.
git branch -a
git checkout -b development
git push --set-upstream origin development
##############################################################################
# merge master into development, qirc.
cd ~/projects/qirc-code
git checkout development
git merge master
git push
##############################################################################
# merge development into master, qirc.
cd ~/projects/qirc-code
git checkout master
git merge development
git push
git checkout development
##############################################################################
# check diffs, qirc.
cd ~/projects/qirc-code
git diff
##############################################################################
# delete the development branch, qirc.
git branch -d development
git push origin :development
git fetch -p 
##############################################################################
# undo, changes, qirc, github.
cd ~/projects/qirc-code
git checkout *
##############################################################################
# install, qirc.
sudo bash -i
cd /home/tau/projects/qirc-code
python2 setup.py install
rm -fr build
exit
##############################################################################
# build, qirc, package, disutils.
cd /home/tau/projects/qirc-code
python2.6 setup.py sdist 
rm -fr dist
rm MANIFEST
##############################################################################
# share, put, place, host, package, python, pip, application, qirc.

cd ~/projects/qirc-code
python2 setup.py sdist register upload
rm -fr dist
##############################################################################


