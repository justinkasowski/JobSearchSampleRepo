@echo off
echo Stopping containers and removing project volumes...
docker compose down -v

echo Removing project API image...
docker image rm jobsearchsamplerepo-api 2>nul

echo Removing dangling images created during build...
docker image prune -f

echo Uninstall complete.
pause