import unittest
import os
import tarfile
import json
from emulator import Emulator
from unittest import mock
from io import StringIO
from collections import deque

class TestEmulator(unittest.TestCase):
    def setUp(self):
        # Создаем временные файлы для тестов
        self.config_path = 'test_config.yaml'
        self.log_file_path = 'test_logs.json'
        self.virtual_fs_path = 'test_virtual_fs.tar'

        # Создаем конфигурационный файл
        with open(self.config_path, 'w') as f:
            f.write(f'virtual_fs_path: "{self.virtual_fs_path}"\n')
            f.write(f'log_file_path: "{self.log_file_path}"\n')

        # Создаем пустой лог-файл
        with open(self.log_file_path, 'w') as f:
            f.write('{"actions": []}')

        # Создаем структуру виртуальной файловой системы
        os.makedirs('test_virtual_fs/documents', exist_ok=True)
        os.makedirs('test_virtual_fs/images', exist_ok=True)
        os.makedirs('test_virtual_fs/empty_dir', exist_ok=True)
        with open('test_virtual_fs/documents/file1.txt', 'w') as f:
            f.write('Test file 1')
        with open('test_virtual_fs/images/photo1.png', 'w') as f:
            f.write('Test photo 1')

        # Упаковываем в tar-архив
        with tarfile.open(self.virtual_fs_path, 'w') as tar:
            tar.add('test_virtual_fs', arcname='virtual_fs')

        # Инициализируем эмулятор
        self.emulator = Emulator(config_path=self.config_path)

    def tearDown(self):
        # Удаляем временные файлы и директории после тестов
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        if os.path.exists(self.log_file_path):
            os.remove(self.log_file_path)
        if os.path.exists(self.virtual_fs_path):
            os.remove(self.virtual_fs_path)
        if os.path.exists('test_virtual_fs'):
            import shutil
            shutil.rmtree('test_virtual_fs')

    @mock.patch('builtins.print')
    def test_ls_non_empty_dir(self, mock_print):
        self.emulator.current_path = deque(['/'])
        self.emulator.ls([])
        expected = sorted(['documents    root', 'images    root', 'empty_dir    root'])
        actual = sorted([call.args[0] for call in mock_print.call_args_list])
        self.assertEqual(actual, expected)

    @mock.patch('builtins.print')
    def test_ls_empty_dir(self, mock_print):
        self.emulator.current_path = deque(['/empty_dir'])
        self.emulator.ls([])
        mock_print.assert_not_called()

    @mock.patch('builtins.print')
    def test_ls_invalid_dir(self, mock_print):
        self.emulator.ls(['nonexistent'])
        mock_print.assert_called_with('ls: невозможно получить доступ к "/nonexistent": Нет такого файла или каталога')

    @mock.patch('builtins.print')
    def test_logging_action(self, mock_print):
        self.emulator.ls([])
        with open(self.log_file_path, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
        last_action = log_data['actions'][-1]
        self.assertEqual(last_action['command'], 'ls')
        self.assertEqual(last_action['arguments'], [])

    @mock.patch('builtins.print')
    def test_multiple_logging_actions(self, mock_print):
        self.emulator.ls([])
        self.emulator.cd(['documents'])
        self.emulator.chown(['user123', 'documents/file1.txt'])
        with open(self.log_file_path, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
        self.assertEqual(len(log_data['actions']), 3)
        self.assertEqual(log_data['actions'][0]['command'], 'ls')
        self.assertEqual(log_data['actions'][1]['command'], 'cd')
        self.assertEqual(log_data['actions'][2]['command'], 'chown')

if __name__ == '__main__':
    unittest.main()
