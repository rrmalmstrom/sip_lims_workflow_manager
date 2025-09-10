@echo off
echo --- Updating Workflow Scripts ---

cd scripts
set "GIT_SSH_COMMAND=ssh -i ..\.ssh\deploy_key -o IdentitiesOnly=yes"
git pull
set GIT_SSH_COMMAND=

echo.
echo Scripts are now up to date.
pause