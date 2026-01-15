### Развертывание проекта на удаленном сервере:  

1. Подключиться к серверу через SSH:  
  `ssh -i <путь до id_rsa ключа на локальном устройстве>/id_rsa <username на сервере>@<ip-адрес сервера>`  
  Ввести `<passphrase>` для подключения к серверу при наличии.  
2. На сервере создать директорию VolleyBolley.  
3. Скопировать на сервер в директорию VolleyBolley файл .env по образцу в файле infra/.env.example для production.  
4. Установить docker на сервере:
  ```
  sudo apt update  
  sudo apt install curl  
  curl -fSL https://get.docker.com -o get-docker.sh  
  sudo sh ./get-docker.sh  
  sudo apt install docker-compose-plugin  
  sudo usermod -aG docker <username>  
  newgrp docker  
  sudo systemctl restart docker  
  ```
5. Обновить secrets в настройках репозитория при необходимости:  
  - SECRET_KEY  
  - ALLOWED_HOSTS  
  - HOST  
  - USER  
  - SSH_KEY  
  - TELEGRAM_TO  
  - TELEGRAM_TOKEN  
6. Сделать push в ветку main.  
  
### Запуск проекта локально:  
1. Клонировать репозиторий.  
2. Создать `.env` файл в директории infra/ по образцу `.env.example` для docker-compose.yml.  
3. Запустить локально Docker engine.  
4. Перейти в директорию infra/ и выполнить команду `docker-compose up`.  
   
### Запуск проекта для разработки:  
1. Клонировать репозиторий.  
2. Создать и активировать виртуальное окружение:  
  - перейти в директорию backend `cd backend`  
  - создать виртуальное окружение `python -m venv venv`  
  - активировать виртуальное окружение `source venv/Scripts/activate`  
3. Установить poetry `pip install poetry`.  
4. Установить зависимости: `poetry install`.  
  
### Запуск линтера  
```
poetry run ruff check {название файла/путь до директории}
```
  
### Запуск тестов:  
1. Активировать виртуальное окружение.  
2. Создать в директории infra/ файл .env.  
3. Копировать в файл .env пример из env.example для тестирования.  
4. Запустить локально Docker engine.  
5. Перейти в директорию infra/ и выполнить команду `docker-compose -f docker-compose-dev.yml up`.  
6. Открыть новое окно терминала, перейти в директорию backend/ и выполнить команду `pytest`.  
   
### Обновление проекта, развернутого на сервере:    
1. Для обновления проекта на сервере необходимо сделать push в ветку main.  
