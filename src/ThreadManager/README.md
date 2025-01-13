# ThreadManager

`ThreadManager` — это простой менеджер пула потоков на, предназначенный для управления выполнением асинхронных задач. Он предоставляет возможность добавлять задачи с приоритетами, останавливать отдельные группы задач, изменять размер пула потоков во время выполнения и ожидать завершения всех задач.

## Возможности

*   **Управление пулом потоков:** Создание и управление пулом потоков заданного размера.
*   **Добавление задач:** Добавление задач (функций или лямбда-выражений) в очередь на выполнение.
*   **Приоритеты задач:** Поддержка приоритетов задач (`High`, `Normal`, `Low`). Задачи с более высоким приоритетом выполняются первыми.
*   **Группы задач:** Возможность группировать задачи и останавливать выполнение целых групп.
*   **Изменение размера пула:** Динамическое изменение количества потоков в пуле во время выполнения.
*   **Ожидание завершения:** Метод `waitForAll()` для синхронного ожидания завершения всех задач в очереди.
*   **Безопасность потоков:** Использование мьютексов и условных переменных для обеспечения корректной работы в многопоточной среде.

### Пример использования

```c++
#include "ThreadManager.hpp"
#include <iostream>
#include <chrono>
#include <thread>

void heavyTask(size_t taskId, int computationLimit) {
    volatile int result = 0;
    for (int i = 0; i < computationLimit; ++i) {
        result += i;
    }
    std::cout << "Task " << taskId << " finished.\n";
}

int main() {
    const size_t numThreads = 4;
    const size_t numTasks = 10;
    const int computationLimit = 10000000;

    ThreadManager threadManager(numThreads);

    auto start = std::chrono::high_resolution_clock::now();

    for (size_t i = 0; i < numTasks; ++i) {
        if (i%3 == 0) {
            threadManager.addTask([i, computationLimit]() { heavyTask(i, computationLimit); }, ThreadManager::TaskPriority::High);
        } else if (i%3 == 1) {
            threadManager.addTask([i, computationLimit]() { heavyTask(i, computationLimit); }, ThreadManager::TaskPriority::Normal);
        } else {
            threadManager.addTask([i, computationLimit]() { heavyTask(i, computationLimit); }, ThreadManager::TaskPriority::Low);
        }
    }

    threadManager.waitForAll(); // Ожидаем завершения всех задач
    threadManager.stopAll(); // Останавливаем потоки

    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> duration = end - start;

    std::cout << "Total execution time: " << duration.count() << " seconds\n";

    return 0;
}
```

В этом примере создается `ThreadManager` с 4 потоками и добавляется 10 задач с разными приоритетами. `threadManager.waitForAll()` гарантирует, что программа дождется выполнения всех задач перед завершением.

### Методы

*   `ThreadManager(size_t maxThreads = std::thread::hardware_concurrency())`: Конструктор. Создает пул из `maxThreads` потоков. По умолчанию использует количество аппаратных ядер.
*   `addTask(const Task& task, TaskPriority priority = TaskPriority::Normal, size_t groupID = 0)`: Добавляет задачу в очередь.
*   `stopAll()`: Останавливает все потоки.
*   `stopGroup(size_t groupID)`: Останавливает выполнение задач указанной группы.
*   `resizeThreadPool(size_t newSize)`: Изменяет размер пула потоков.
*   `waitForAll()`: Ожидает завершения всех задач в очереди.

