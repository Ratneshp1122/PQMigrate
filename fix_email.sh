cd /home/ratneshp0411/pqc_migration_tool
git stash
git filter-branch -f --env-filter '
if [ "$GIT_AUTHOR_EMAIL" = "ratneshp0411@pqmigrate" ]; then
    export GIT_AUTHOR_EMAIL="ratneshp1108@gmail.com"
fi
if [ "$GIT_COMMITTER_EMAIL" = "ratneshp0411@pqmigrate" ]; then
    export GIT_COMMITTER_EMAIL="ratneshp1108@gmail.com"
fi
' HEAD
git stash pop
