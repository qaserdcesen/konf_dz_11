# Эмулятор оболочки UNIX-подобной ОС

## Библиотеки, не входящие в стандартную библиотеку Python

- **yaml**: Модуль из внешней библиотеки `PyYAML`, используемый для работы с конфигурационными файлами формата YAML.
- **psutil**: Внешняя библиотека для получения системной информации, включая время работы системы (uptime).

---

## 1. Общее описание

Данный проект представляет собой **эмулятор языка оболочки операционной системы**, работающий в режиме командной строки (CLI). Он предназначен для имитации работы shell в UNIX-подобной ОС, предоставляя пользователю возможность выполнять команды в рамках виртуальной файловой системы, представленной в виде tar-архива.

**Особенности:**
- Поддержка основных команд оболочки: `ls`, `cd`, `exit`.
- Дополнительные команды: `chown`, `date`, `uptime`.
- Виртуальная файловая система не требует предварительного распаковки архива.
- Логирование действий пользователя с фиксацией времени в формате JSON.

---

## 2. Описание всех функций и настроек

### Основные компоненты

- **`emulator.py`**: Главный скрипт эмулятора, реализующий весь функционал.
- **`config.yaml`**: Конфигурационный файл в формате YAML.
- **`log.json`**: Лог-файл в формате JSON, содержащий записи всех действий пользователя.

---

### Функции

#### Загрузка конфигурации

```python
def load_config():
    with open('config.yaml', 'r') as file:
        return yaml.safe_load(file)
```
Описание: Загружает настройки из файла config.yaml, включая пути к виртуальной файловой системе и лог-файлу.

#### Логирование действий

```python
def log_action(action, log_path):
    timestamp = datetime.datetime.now().isoformat()
    log_entry = {"timestamp": timestamp, "action": action}

    if os.path.exists(log_path):
        with open(log_path, 'r') as logfile:
            try:
                log_data = json.load(logfile)
            except json.JSONDecodeError:
                log_data = []
    else:
        log_data = []

    log_data.append(log_entry)

    with open(log_path, 'w') as logfile:
        json.dump(log_data, logfile, indent=4)
```
Описание: Записывает действия пользователя в лог-файл log.json с указанием времени выполнения.

#### Извлечение виртуальной файловой системы

```python
def extract_tar(tar_path, extract_path, log_path):
    with tarfile.open(tar_path, 'r') as tar:
        tar.extractall(path=extract_path)
    log_action(f'Extracted {tar_path}', log_path)
```
Описание: Извлекает виртуальную файловую систему из tar-архива.


---


### Команды

#### Команда ls

```python
def ls(current_path, log_path):
    entries = os.listdir(current_path)
    print(" ".join(entries))
    log_action('Executed ls command', log_path)
```
Описание: Отображает содержимое текущего каталога.


#### Команда cd

```python
def cd(directory, current_path):
    new_path = os.path.join(current_path, directory)
    if os.path.isdir(new_path):
        return os.path.abspath(new_path)
    else:
        print(f"cd: no such directory: {directory}")
        return current_path
```
Описание: Изменяет текущий каталог на указанный.


#### Команда exit

```python
    def exit(self):
        self.log_action('exit', [])
        print("Exiting...")
        sys.exit(0)
```
Описание: Завершает сеанс работы эмулятора.

#### Команда chown

```python
def chown(user, file, current_path, log_path):
    file_path = os.path.join(current_path, file)
    if os.path.exists(file_path):
        print(f"Changed owner of {file} to {user}")
        log_action(f'Changed owner of {file} to {user}', log_path)
    else:
        print(f"chown: cannot access '{file}': No such file or directory")
```
Описание: Эмулирует изменение владельца указанного файла или каталога.

#### Команда date

```python
def date_command(log_path):
    current_date = datetime.datetime.now()
    print(current_date.strftime("%Y-%m-%d %H:%M:%S"))
    log_action('Executed date command', log_path)
```
Описание: Отображает текущую дату и время.

#### Команда uptime

```python
def uptime_command(log_path):
    uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())
    print(f"Uptime: {uptime.days}d {uptime.seconds // 3600}h {(uptime.seconds % 3600) // 60}m")
    log_action('Executed uptime command', log_path)
```
Описание: Выводит время работы системы с момента последней загрузки.


---


### Настрйоки

#### Файл config.yaml

```yaml
virtual_fs_path: "virtual_fs.tar"
log_file_path: "log.json"
```

- `virtual_fs_path`: Указывает путь к архиву виртуальной файловой системы.
- `log_file_path`: Указывает путь к JSON-файлу, где записываются действия пользователя.


---


## 4. Примеры использования

### Использование команды ls
![image](https://github.com/user-attachments/assets/bd7b2be1-934d-4e3a-b473-2bb86b459143)

### Использование команды cd
![image](https://github.com/user-attachments/assets/dd45f77f-1064-477a-b3ad-8855ed71a217)

### Использование команды chown
![image](https://github.com/user-attachments/assets/3409aa8d-dcce-4d0e-828d-3626c1e0ce8f)

### Использование команды date
![image](https://github.com/user-attachments/assets/4c474a85-a65c-45d9-8926-9d8c63c7c8b5)

### Использование команды uptime
![image](https://github.com/user-attachments/assets/de26261b-11d0-4fad-9863-09856a3e5d0a)

### Использование команды exit
![image](https://github.com/user-attachments/assets/ad663e42-5023-41ec-ae37-aef48c68ea96)



---


## 5. Результаты тестирования

после запуска комнады
```python
python -m unittest discover -s tests
```

![image](https://github.com/user-attachments/assets/93dc267b-11eb-406e-a633-f346e1d69817)


Покрытие тестов:

- `test_ls`: Проверяет корректность вывода команды `ls`.
- `test_cd_valid_directory`: Проверяет переход в существующий каталог.
- `test_cd_invalid_directory`: Проверяет обработку несуществующего каталога.
- `test_cd_parent_directory`: Проверяет переход в родительский каталог.
- `test_exit`: Проверяет корректность завершения работы эмулятора.
- `test_chown_existing_file`: Проверяет изменение владельца существующего файла.
- `test_chown_nonexistent_file`: Проверяет обработку несуществующего файла.
- `test_date`: Проверяет вывод текущей даты и времени.
- `test_uptime`: Проверяет вывод времени работы системы.


