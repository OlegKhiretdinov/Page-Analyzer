# Page Analyzer
Сервис анализирует указанные страницы. Проверяет код ответа и наличие некоторых тегов.

### Hexlet tests and linter status:
[![Actions Status](https://github.com/OlegKhiretdinov/python-project-83/workflows/hexlet-check/badge.svg)](https://github.com/OlegKhiretdinov/python-project-83/actions)
[![Maintainability](https://api.codeclimate.com/v1/badges/213958da23a1aef881ae/maintainability)](https://codeclimate.com/github/OlegKhiretdinov/python-project-83/maintainability)

### Requirement

Python 3.10  
Pip 23  
Poetry 1.4  
PostgreSQL 16.1

### Установка
1. Склонировать
2. В директории проекта выполнить:  
   `make install`  
   `make build`
3. В корень проекта добавить файл .env и прописать DATABASE_URL(строка с параметрами подключения к базе данных) и SECRET_KEY

### Work example
[demo](https://page-analyzer-clm3.onrender.com)