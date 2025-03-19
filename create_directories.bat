@echo off
REM Create main project directory structure

mkdir services
mkdir models
mkdir routes
mkdir static\css
mkdir static\js
mkdir static\img\icons
mkdir templates\pdf
mkdir templates\components
mkdir templates\convert
mkdir templates\legal
mkdir templates\errors
mkdir utils
mkdir tasks
mkdir temp

REM Create __init__.py files in package directories
echo. > services\__init__.py
echo. > models\__init__.py
echo. > routes\__init__.py
echo. > utils\__init__.py
echo. > tasks\__init__.py

echo Directory structure created successfully!