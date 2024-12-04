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
    def load_config(self, config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                self.config = yaml.safe_load(file)
            if 'virtual_fs_path' not in self.config or 'log_file_path' not in self.config:
                raise KeyError("Конфигурационный файл должен содержать 'virtual_fs_path' и 'log_file_path'.")
        except FileNotFoundError:
            print(f"Конфигурационный файл '{config_path}' не найден.")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"Ошибка парсинга YAML: {e}")
            sys.exit(1)
        except KeyError as e:
            print(f"Ошибка конфигурации: {e}")
            sys.exit(1)
```
Описание: Загружает настройки из файла config.yaml, включая пути к виртуальной файловой системе и лог-файлу.

#### Логирование действий

```python
    def log_action(self, command, args):
        if self.debug:
            print(f"[DEBUG] Logging action: {command} {args}")
        action = {
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'arguments': args
        }
        log_data = {}
        if os.path.isfile(self.log_file_path):
            try:
                with open(self.log_file_path, 'r', encoding='utf-8') as file:
                    log_data = json.load(file)
            except json.JSONDecodeError:
                log_data = {'actions': []}
        else:
            log_data = {'actions': []}
        log_data['actions'].append(action)
        try:
            with open(self.log_file_path, 'w', encoding='utf-8') as file:
                json.dump(log_data, file, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"Ошибка записи в лог-файл: {e}")
```
Описание: Записывает действия пользователя в лог-файл log.json с указанием времени выполнения.

#### Загружает виртуальную файловую систему из архива

```python
    def load_virtual_fs(self):
        self.root = FileSystemNode('/', is_dir=True)
        tar_path = os.path.abspath(self.config['virtual_fs_path']).replace('\\', '/')
        if not os.path.isfile(tar_path):
            print(f"Архив виртуальной файловой системы '{tar_path}' не найден.")
            sys.exit(1)
        try:
            with tarfile.open(tar_path, 'r') as tar:
                for member in tar.getmembers():
                    if member.name == 'virtual_fs' or not member.name.startswith('virtual_fs/'):
                        continue  # Пропускаем корневую папку
                    path = member.name.replace('virtual_fs/', '', 1).replace('\\', '/')
                    is_dir = member.isdir()
                    self.create_path(path, is_dir)
        except tarfile.TarError as e:
            print(f"Ошибка открытия tar-архива: {e}")
            sys.exit(1)
```

#### Создает директорию или файл по заданному пути в виртуальной файловой системе, разделяя путь на части и итерируя по нему.

```python
        def create_path(self, path, is_dir):
        path = path.replace('\\', '/')
        parts = path.strip('/').split('/')
        current = self.root
        for part in parts[:-1]:
            if part not in current.children:
                current.children[part] = FileSystemNode(part, is_dir=True)
            current = current.children[part]
        last_part = parts[-1]
        if last_part not in current.children:
            current.children[last_part] = FileSystemNode(last_part, is_dir=is_dir)
```


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

### Запуск эмулятора:

```python
python emulator.py
```

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


