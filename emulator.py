import os
import tarfile
import yaml
import json
import sys
from datetime import datetime
from collections import deque

class FileSystemNode:
    def __init__(self, name, is_dir=False, owner='root'):
        self.name = name
        self.is_dir = is_dir
        self.owner = owner
        self.children = {} if is_dir else None

    def __repr__(self):
        return f"{'DIR' if self.is_dir else 'FILE'}: {self.name}, Owner: {self.owner}"

class Emulator:
    def __init__(self, config_path='config.yaml'):
        self.load_config(config_path)
        self.load_virtual_fs()
        self.current_path = deque(['/'])
        self.start_time = datetime.now()
        self.log_file_path = self.config['log_file_path']

    def load_config(self, config_path):
        try:
            with open(config_path, 'r') as file:
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

    def load_virtual_fs(self):
        self.root = FileSystemNode('/', is_dir=True)
        tar_path = self.config['virtual_fs_path']
        if not os.path.isfile(tar_path):
            print(f"Архив виртуальной файловой системы '{tar_path}' не найден.")
            sys.exit(1)
        try:
            with tarfile.open(tar_path, 'r') as tar:
                for member in tar.getmembers():
                    if member.name == 'virtual_fs' or not member.name.startswith('virtual_fs/'):
                        continue  # Пропускаем корневую папку
                    path = member.name.replace('virtual_fs/', '', 1)
                    is_dir = member.isdir()
                    self.create_path(path, is_dir)
        except tarfile.TarError as e:
            print(f"Ошибка открытия tar-архива: {e}")
            sys.exit(1)

    def create_path(self, path, is_dir):
        parts = path.strip('/').split('/')
        current = self.root
        for part in parts[:-1]:
            if part not in current.children:
                current.children[part] = FileSystemNode(part, is_dir=True)
            current = current.children[part]
        last_part = parts[-1]
        if last_part not in current.children:
            current.children[last_part] = FileSystemNode(last_part, is_dir=is_dir)

    def log_action(self, command, args):
        action = {
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'arguments': args
        }
        log_data = {}
        if os.path.isfile(self.log_file_path):
            try:
                with open(self.log_file_path, 'r') as file:
                    log_data = json.load(file)
            except json.JSONDecodeError:
                log_data = {'actions': []}
        else:
            log_data = {'actions': []}
        log_data['actions'].append(action)
        try:
            with open(self.log_file_path, 'w') as file:
                json.dump(log_data, file, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"Ошибка записи в лог-файл: {e}")

    def parse_command(self, input_str):
        parts = input_str.strip().split()
        if not parts:
            return None, []
        return parts[0], parts[1:]

    def run(self):
        while True:
            try:
                prompt = self.get_prompt()
                command_input = input(prompt)
                command, args = self.parse_command(command_input)
                if not command:
                    continue
                self.log_action(command, args)
                if command == 'ls':
                    self.ls(args)
                elif command == 'cd':
                    self.cd(args)
                elif command == 'exit':
                    self.exit()
                elif command == 'chown':
                    self.chown(args)
                elif command == 'date':
                    self.date()
                elif command == 'uptime':
                    self.uptime()
                else:
                    print(f'Команда "{command}" не распознана.')
            except KeyboardInterrupt:
                print('\nИспользуйте команду "exit" для выхода.')
            except Exception as e:
                print(f'Ошибка: {e}')

    def get_prompt(self):
        return ''.join(self.current_path) + '$ '

    def ls(self, args):
        target_path = self.get_target_path(args)
        node = self.get_node(target_path)
        if node is None:
            print(f'ls: невозможно получить доступ к "{target_path}": Нет такого файла или каталога')
            return
        if not node.is_dir:
            print(node.name)
            return
        for name in sorted(node.children.keys()):
            print(name)

    def cd(self, args):
        if not args:
            self.current_path = deque(['/'])
            return
        target = args[0]
        if target == '/':
            self.current_path = deque(['/'])
            return
        elif target == '..':
            if len(self.current_path) > 1:
                self.current_path.pop()
            return
        else:
            new_path = self.resolve_path(target)
            node = self.get_node(new_path)
            if node and node.is_dir:
                self.current_path = deque(new_path.strip('/').split('/'))
                if not self.current_path:
                    self.current_path = deque(['/'])
                else:
                    self.current_path.appendleft('/')
            else:
                print(f'cd: невозможен переход в "{target}": Нет такого каталога')

    def exit(self):
        print('Выход из эмулятора.')
        sys.exit(0)

    def chown(self, args):
        if len(args) != 2:
            print('Использование: chown <новый_владелец> <путь>')
            return
        new_owner, path = args
        target_path = self.resolve_path(path)
        node = self.get_node(target_path)
        if node:
            node.owner = new_owner
            print(f'Владелец "{path}" изменен на "{new_owner}".')
        else:
            print(f'chown: невозможно изменить владельца "{path}": Нет такого файла или каталога')

    def date(self):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(now)

    def uptime(self):
        now = datetime.now()
        delta = now - self.start_time
        uptime_str = self.format_timedelta(delta)
        print(f'Uptime: {uptime_str}')

    def format_timedelta(self, delta):
        days, seconds = delta.days, delta.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{days}д {hours}ч {minutes}м {seconds}с"

    def get_target_path(self, args):
        if not args:
            return self.get_current_path()
        path = args[0]
        if path.startswith('/'):
            return path
        else:
            return os.path.join(self.get_current_path(), path).replace('//', '/')

    def resolve_path(self, path):
        if path.startswith('/'):
            return path
        else:
            current = self.get_current_path()
            return os.path.join(current, path).replace('//', '/')

    def get_current_path(self):
        if len(self.current_path) == 1 and self.current_path[0] == '/':
            return '/'
        else:
            return '/' + '/'.join(list(self.current_path)[1:])

    def get_node(self, path):
        if path == '/':
            return self.root
        parts = path.strip('/').split('/')
        current = self.root
        for part in parts:
            if not current.is_dir:
                return None
            if part in current.children:
                current = current.children[part]
            else:
                return None
        return current

if __name__ == '__main__':
    emulator = Emulator()
    emulator.run()