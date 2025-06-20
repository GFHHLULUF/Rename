#!/usr/bin/env python3
"""
Скрипт для запуска всех тестов с отчетом о покрытии
"""

import os
import sys
import subprocess
import coverage

def run_tests_with_coverage():
    """Запуск тестов с измерением покрытия кода"""
    
    # Настройка покрытия
    cov = coverage.Coverage(
        source=['models', 'views'],
        omit=[
            '*/tests/*',
            '*/__pycache__/*',
            '*/venv/*',
            '*/env/*'
        ]
    )
    
    # Начинаем измерение покрытия
    cov.start()
    
    # Запускаем тесты
    print("Запуск тестов...")
    test_result = subprocess.run([
        sys.executable, '-m', 'pytest', 
        'tests/', 
        '-v', 
        '--tb=short'
    ], capture_output=True, text=True)
    
    # Останавливаем измерение покрытия
    cov.stop()
    cov.save()
    
    # Выводим результаты тестов
    print("Результаты тестов:")
    print(test_result.stdout)
    if test_result.stderr:
        print("Ошибки:")
        print(test_result.stderr)
    
    # Анализируем покрытие
    print("\n" + "="*50)
    print("ОТЧЕТ О ПОКРЫТИИ КОДА")
    print("="*50)
    
    # Получаем статистику покрытия
    cov.report()
    
    # Сохраняем HTML отчет
    cov.html_report(directory='htmlcov')
    print(f"\nHTML отчет сохранен в папке: htmlcov/")
    
    # Получаем процент покрытия
    total_statements = 0
    total_missing = 0
    
    for filename in cov.get_data().measured_files():
        if 'models' in filename or 'views' in filename:
            analysis = cov.analysis2(filename)
            total_statements += len(analysis[1])  # statements
            total_missing += len(analysis[2])     # missing
    
    if total_statements > 0:
        coverage_percentage = ((total_statements - total_missing) / total_statements) * 100
        print(f"\nОбщее покрытие кода: {coverage_percentage:.1f}%")
        
        if coverage_percentage >= 50:
            print("✅ Покрытие кода >= 50% - ТРЕБОВАНИЕ ВЫПОЛНЕНО")
        else:
            print("❌ Покрытие кода < 50% - ТРЕБОВАНИЕ НЕ ВЫПОЛНЕНО")
    else:
        print("❌ Не удалось измерить покрытие кода")
    
    return test_result.returncode == 0

def run_specific_test(test_file):
    """Запуск конкретного теста"""
    print(f"Запуск теста: {test_file}")
    result = subprocess.run([
        sys.executable, '-m', 'pytest', 
        f'tests/{test_file}', 
        '-v'
    ])
    return result.returncode == 0

def main():
    """Главная функция"""
    print("Тестирование системы мониторинга серверов")
    print("="*50)
    
    if len(sys.argv) > 1:
        # Запуск конкретного теста
        test_file = sys.argv[1]
        success = run_specific_test(test_file)
    else:
        # Запуск всех тестов с покрытием
        success = run_tests_with_coverage()
    
    if success:
        print("\n✅ Все тесты прошли успешно!")
        sys.exit(0)
    else:
        print("\n❌ Некоторые тесты не прошли!")
        sys.exit(1)

if __name__ == '__main__':
    main() 