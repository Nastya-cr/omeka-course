# Учебный стенд Omeka S

Две коллекции, одна установка Omeka S и пять сервисов. Проект использует официальный выпуск Omeka S 4.2.1, собственный Dockerfile с PHP/Apache, Nginx, MariaDB, BusyBox и клиент MariaDB для копирования. Скачанную отдельно Docker-сборку можно оставить в папке загрузок. Для этой курсовой запускай файлы из данной папки.

## 1. Локальный запуск на macOS

Открой Docker Desktop. В Терминале набери `cd `, перетащи папку `practice` в окно и нажми Enter. Выполни по одной строке:

```sh
docker version
docker compose version
sh scripts/init-secrets.sh
docker compose config -q
docker compose up -d --build
docker compose ps
sh scripts/smoke.sh
```

Первая сборка скачивает базовые образы, системные пакеты и ZIP Omeka S. Если порт 8080 занят, используй `export LIBRARY_PORT=8081` перед запуском и замени порт в адресе и командах. Пароли MariaDB создаются локально и повторно используются. Для macOS Terminal на Apple Silicon сборка выполняется для локальной архитектуры.

Открой http://127.0.0.1:8080/admin. Заполни поля первого администратора, задай имя установки и выбери нужный язык. Пароль администратора придумывается отдельно от секретов MariaDB. Если видишь 502, проверь `docker compose ps` и `docker compose logs --tail=60 proxy omeka db`. Если не собирается образ, сохрани последние строки вывода сборки.

## 2. Первая демонстрация

1. В «Item Sets» создай наборы «Библиотека» и «Архив». Для публичного примера сделай их видимыми.
2. В «Items» нажми «Add new item». Добавь названия и автора из `samples/catalog.csv`. На вкладке Media прикрепи PDF, на вкладке Item Sets укажи набор.
3. Создай сайт «Электронная библиотека и архив». Проверь, что обе карточки добавлены к этому сайту и видимы. Открой «Browse items», найди слово «Библиотечный» и открой PDF.
4. Создай отдельную учётную запись с ролью Researcher. Через администратора можно задать временный пароль, если на стенде не настроена отправка писем. Проверь, что под этой ролью нет кнопки создания карточки. Для сравнения проверь роль Editor.
5. Сделай дополнительную карточку с тестовым названием и статусом private. Убедись, что публичный поиск её не показывает. На стенде используются только учебные файлы. Для конфиденциальных файлов дополнительно проверяют прямые URL и проектируют отдельный механизм выдачи.

Сними реальные скриншоты каталога, карточки, результата поиска и вывода `docker compose ps`. Имена файлов для отчёта и слайда приведены в `evidence/README.md`.

## 3. Копия и восстановление

Создай согласованную копию, когда редакторы прекратили работу. Остановка Omeka S на время этой операции исключает записи приложения между дампом и упаковкой файлов.

```sh
docker compose stop omeka
docker compose exec -T backup sh /usr/local/bin/backup.sh
docker compose start omeka
docker compose exec -T backup ls -1 /backups
```

Если копирование завершилось ошибкой, всё равно запусти Omeka S обратно. Запиши имя только что созданной копии в переменную и экспортируй её. Команда ниже требует заменить имя каталога.

```sh
copy_name='ИМЯ_КАТАЛОГА_КОПИИ'
mkdir -p copies
docker compose cp "backup:/backups/$copy_name" copies/
```

Проверь контрольные суммы внутри контейнера: `docker compose exec -T backup sh -c 'cd "/backups/$1" && sha256sum -c SHA256SUMS' sh "$copy_name"`. Храни экспортированную копию отдельно от узла с данными. Сервис делает очередную копию через 24 часа после запуска или предыдущей попытки. Такой запуск не блокирует записи в приложение. Для контрольного восстановления используй копию, сделанную при остановленном приложении. Старые копии удаляются вручную после проверки внешнего экземпляра.

Восстановление выполняется в отдельный Compose-проект на порту 8081. Для чистой пробы выбери новое имя проекта. Сначала проверь суммы оригинала.

```sh
export LIBRARY_PORT=8081
docker compose -p library-restore up -d --wait db
docker compose -p library-restore exec -T db sh -ec '
  MYSQL_PWD=$(cat /run/secrets/omeka_db_password) mariadb -uomeka omeka
' < "copies/$copy_name/database.sql"
docker compose -p library-restore run --rm --no-deps -T --entrypoint /bin/sh omeka -ec '
  tar -xzf - -C /var/www/html/files
  chown -R www-data:www-data /var/www/html/files
' < "copies/$copy_name/files.tar.gz"
docker compose -p library-restore up -d
sh scripts/smoke.sh http://127.0.0.1:8081
```

В восстановленной копии открой обе карточки, проверь данные и скачай оригиналы. Для исходного стенда снова используй 8080. Переменную можно очистить командой `unset LIBRARY_PORT`.

## 4. Два узла Docker Swarm

Используй две Linux ВМ в одной частной сети с установленным Docker Engine. На Mac их можно запустить в гипервизоре или использовать удалённые ВМ. Для каждой выдели как ориентир 2 vCPU, 4 ГБ ОЗУ и 20 ГБ диска. Разреши между узлами TCP 2377, TCP/UDP 7946 и UDP 4789. Пользовательский HTTP-порт 8080 доступен только в сети стенда. Команды управления выполняются на manager.

```sh
docker swarm init --advertise-addr IP_MANAGER
docker swarm join-token worker
```

На worker выполни команду присоединения, которую вывел manager. На manager задай метки по именам узлов из `docker node ls`. Узел с данными должен быть ровно один. Для одноузловой пробы обе метки можно дать одному узлу.

```sh
docker node update --label-add library_data=true ИМЯ_MANAGER
docker node update --label-add library_edge=true ИМЯ_WORKER
sh scripts/init-secrets.sh
docker secret create omeka_db_password .secrets/omeka_db_password
docker secret create omeka_root_password .secrets/omeka_root_password
```

Команды создания секретов выполняются один раз. Повторное развёртывание использует существующие секреты. Укажи реальный опубликованный образ из Actions и войди в GHCR, если образ закрытый.

```sh
export OMEKA_IMAGE=ghcr.io/владелец/репозиторий/omeka:SHA_КОММИТА
docker stack config -c stack.yaml > /dev/null
docker stack deploy --with-registry-auth -c stack.yaml library
docker stack services library
docker stack ps library
docker network inspect library_front library_back
sh scripts/smoke.sh
```

Открывай сайт с Mac по `http://IP_УЗЛА:8080/admin`. Том Compose и том Swarm создаются независимо. Для демонстрации в кластере заново добавь тестовые материалы. Для переноса используй проверенную пару «дамп и файлы» и подходящую процедуру импорта на узле данных. Метка закрепляет локальные тома за одним узлом. Утрата этого узла требует восстановления данных из копии.

При ручном изменении файлов, объявленных в Swarm configs, меняй `CONFIG_REV` перед деплоем. Это создаёт новые объекты конфигурации, а старые версии после проверки можно удалить, если они больше не используются.

## 5. CI/CD

В корень приватного GitHub-репозитория помести содержимое папки `practice`, включая `.github` и `.gitignore`. После push в main workflow проверяет локальный стенд, создаёт тестовую копию, собирает образ для amd64 и arm64 и публикует его в GHCR с тегом SHA. Для доставки на учебный кластер зарегистрируй собственный runner на manager с меткой `library-swarm`, доступом к Docker и установленным curl. Настрой права workflow на пакет GHCR. В Actions запусти workflow из main с флажком Deploy this version to the teaching cluster. Self-hosted runner используется только в задании доставки и только для доверенного кода main. Для первого ручного запуска можно использовать опубликованный тег без runner.

В CI доступность страницы установки проверяется до заполнения администратора. Действия с карточками, роли, содержимое базы и восстановление пользовательских данных проверяются отдельно по протоколу.

## 6. Что показать на защите

`docker compose ps`, `docker compose logs --tail=10 monitor`, публичный поиск и карточку, `docker node ls`, `docker stack services library`, строку успешного workflow и восстановленную карточку. Отдельно покажи, что бэкап содержит SQL, архив файлов и контрольные суммы. Схема архитектуры и файл речи находятся в корне комплекта.
