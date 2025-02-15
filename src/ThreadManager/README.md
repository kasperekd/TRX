# ThreadManager
`ThreadManager` — это простой менеджер пула потоков, предназначенный для управления выполнением асинхронных задач. Он предоставляет возможность добавлять задачи с приоритетами, останавливать отдельные группы задач, изменять размер пула потоков во время выполнения и ожидать завершения всех задач.

## Возможности
*   **Управление пулом потоков:** Создание и управление пулом потоков заданного размера.
*   **Добавление задач:** Добавление задач (функций или лямбда-выражений) в очередь на выполнение.
*   **Приоритеты задач:** Поддержка приоритетов задач (`High`, `Normal`, `Low`). Задачи с более высоким приоритетом выполняются первыми.
*   **Группы задач:** Возможность группировать задачи и останавливать выполнение целых групп.
*   **Изменение размера пула:** Динамическое изменение количества потоков в пуле во время выполнения.
*   **Ожидание завершения:** Методы `waitForAll()` и `waitForTask()` для синхронного ожидания завершения всех задач или конкретной задачи.
*   **Безопасность потоков:** Использование мьютексов и условных переменных для обеспечения корректной работы в многопоточной среде.

### Пример использования

#### Пример с `waitForAll`
```c++
#include "ThreadManager.hpp"
#include <iostream>
#include <chrono>
#include <cmath>

bool isPrime(int number) {
    if (number <= 1) return false;
    for (int i = 2; i <= std::sqrt(number); ++i) {
        if (number % i == 0) return false;
    }
    return true;
}

size_t heavyTask(size_t taskId, int computationLimit) {
    int count = 0;
    for (int i = 2; i < computationLimit; ++i) {
        if (isPrime(i)) ++count;
    }
    std::cout << "Task " << taskId << " finished, primes counted: " << computationLimit << "\n";
    return count;
}

int main() {
    const size_t numThreads = 4;
    const size_t numTasks = 10;
    const int computationLimit = 1000000;
    ThreadManager threadManager(numThreads);
    auto start = std::chrono::high_resolution_clock::now();
    std::vector<size_t> taskIDs;
    for (size_t i = 0; i < numTasks; ++i) {
        if (i % 3 == 0) {
            taskIDs.push_back(threadManager.addTask<size_t>(
                [i, computationLimit]() { return heavyTask(i, computationLimit); },
                ThreadManager::TaskPriority::High));
        } else if (i % 3 == 1) {
            taskIDs.push_back(threadManager.addTask<size_t>(
                [i, computationLimit]() { return heavyTask(i, computationLimit); },
                ThreadManager::TaskPriority::Normal));
        } else {
            taskIDs.push_back(threadManager.addTask<size_t>(
                [i, computationLimit]() { return heavyTask(i, computationLimit); },
                ThreadManager::TaskPriority::Low));
        }
    }
    auto results = threadManager.waitForAll<size_t>(); // Ожидаем завершения всех задач и получаем результаты
    threadManager.stopAll(); // Останавливаем потоки
    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> duration = end - start;
    std::cout << "Total execution time: " << duration.count() << " seconds\n";

    size_t totalPrimes = 0;
    for (const auto& [taskID, result] : results) {
        totalPrimes += result;
    }
    std::cout << "Total primes counted: " << totalPrimes << "\n";
    return 0;
}
```

В этом примере создается `ThreadManager` с 4 потоками и добавляется 10 задач с разными приоритетами. `threadManager.waitForAll<size_t>()` гарантирует, что программа дождется выполнения всех задач и получит их результаты перед завершением.

#### Пример с `waitForTask`
```c++
#include "ThreadManager.hpp"
#include <iostream>
#include <chrono>
#include <cmath>

bool isPrime(int number) {
    if (number <= 1) return false;
    for (int i = 2; i <= std::sqrt(number); ++i) {
        if (number % i == 0) return false;
    }
    return true;
}

size_t heavyTask(size_t taskId, int computationLimit) {
    int count = 0;
    for (int i = 2; i < computationLimit; ++i) {
        if (isPrime(i)) ++count;
    }
    std::cout << "Task " << taskId << " finished, primes counted: " << computationLimit << "\n";
    return count;
}

int main() {
    const size_t numThreads = 4;
    const size_t numTasks = 10;
    const int computationLimit = 1000000;
    ThreadManager threadManager(numThreads);
    auto start = std::chrono::high_resolution_clock::now();
    std::vector<size_t> taskIDs;
    for (size_t i = 0; i < numTasks; ++i) {
        if (i % 3 == 0) {
            taskIDs.push_back(threadManager.addTask<size_t>(
                [i, computationLimit]() { return heavyTask(i, computationLimit); },
                ThreadManager::TaskPriority::High));
        } else if (i % 3 == 1) {
            taskIDs.push_back(threadManager.addTask<size_t>(
                [i, computationLimit]() { return heavyTask(i, computationLimit); },
                ThreadManager::TaskPriority::Normal));
        } else {
            taskIDs.push_back(threadManager.addTask<size_t>(
                [i, computationLimit]() { return heavyTask(i, computationLimit); },
                ThreadManager::TaskPriority::Low));
        }
    }

    size_t totalPrimes = 0;
    for (size_t taskID : taskIDs) {
        try {
            size_t result = threadManager.waitForTask<size_t>(taskID); // Ожидаем завершения конкретной задачи и получаем результат
            totalPrimes += result;
        } catch (const std::exception& e) {
            std::cerr << "Error waiting for task " << taskID << ": " << e.what() << "\n";
        }
    }

    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> duration = end - start;
    std::cout << "Total execution time: " << duration.count() << " seconds\n";
    std::cout << "Total primes counted: " << totalPrimes << "\n";
    return 0;
}
```

В этом примере создается `ThreadManager` с 4 потоками и добавляется 10 задач с разными приоритетами. Для каждой задачи вызывается `threadManager.waitForTask<size_t>(taskID)`, который ожидает завершения конкретной задачи и получает её результат.

### Методы
*   `ThreadManager(size_t maxThreads = std::thread::hardware_concurrency())`: Конструктор. Создает пул из `maxThreads` потоков. По умолчанию использует количество аппаратных ядер.
*   `addTask<Func, Args...>(Func&& func, Args&&... args, TaskPriority priority = TaskPriority::Normal, size_t groupID = 0)`: Добавляет задачу в очередь. Возвращает идентификатор задачи.
*   `stopAll()`: Останавливает все потоки.
*   `stopGroup(size_t groupID)`: Останавливает выполнение задач указанной группы.
*   `resizeThreadPool(size_t newSize)`: Изменяет размер пула потоков.
*   `waitForAll<ReturnType>()`: Ожидает завершения всех задач в очереди и возвращает карту с идентификаторами задач и их результатами.
*   `waitForTask<ReturnType>(size_t taskID)`: Ожидает завершения конкретной задачи и возвращает её результат.