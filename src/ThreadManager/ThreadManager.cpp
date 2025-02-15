#include "ThreadManager.hpp"

ThreadManager::ThreadManager(size_t maxThreads, bool roundRobin)
    : running(true),
      maxThreads(maxThreads),
      groupRunning(std::bitset<MAX_THREAD_GROUP>().set()),
      tasks_in_queue(0),
      active_threads(0),
      roundRobin(roundRobin),
      nextTaskID(1) {
    std::cout << "ThreadManager started with max " << maxThreads
              << " threads\n";
}

ThreadManager::~ThreadManager() { stopAll(); }

void ThreadManager::stopAll() {
    {
        std::lock_guard<std::mutex> lock(queueMutex);
        running.store(false);
        cv.notify_all();  // Уведомляем всех потоков о завершении
    }
    for (auto& thread : threads) {
        if (thread.joinable()) {
            thread.join();
        }
    }
    threads.clear();
    std::cout << "ThreadManager stopped\n";
}

void ThreadManager::stopGroup(size_t groupID) {
    if (groupID >= MAX_THREAD_GROUP) {
        std::cerr << "Invalid group ID: " << groupID << std::endl;
        return;
    }
    std::bitset<MAX_THREAD_GROUP> expected = groupRunning.load();
    std::bitset<MAX_THREAD_GROUP> desired = expected;
    desired.reset(groupID);  // Сбрасываем нужный бит
    while (!groupRunning.compare_exchange_weak(expected, desired)) {
        desired = expected;
        desired.reset(groupID);
    }
    {
        std::lock_guard<std::mutex> lock(queueMutex);
        std::priority_queue<TaskEntry, std::vector<TaskEntry>,
                            std::greater<TaskEntry>>
            newQueue;
        while (!taskQueue.empty()) {
            auto taskEntry = taskQueue.top();
            taskQueue.pop();
            if (taskEntry.groupID != groupID) {
                newQueue.push(taskEntry);
            }
        }
        taskQueue = std::move(newQueue);
    }
    std::cout << "Group " << groupID << " stopped\n";
}

void ThreadManager::resizeThreadPool(size_t newSize) {
    if (newSize < maxThreads) {
        size_t threadsToStop = maxThreads - newSize;
        {
            std::lock_guard<std::mutex> lock(queueMutex);
            running.store(false);
            cv.notify_all();  // Уведомляем всех потоков о завершении
        }
        for (size_t i = 0; i < threadsToStop; ++i) {
            if (threads.back().joinable()) {
                threads.back().join();
            }
            threads.pop_back();
        }
        maxThreads = newSize;
        {
            std::lock_guard<std::mutex> lock(queueMutex);
            running.store(true);
            cv.notify_all();  // Уведомляем новые потоки о начале работы
        }
    } else {
        maxThreads = newSize;
    }
    std::cout << "Thread pool resized to " << maxThreads << " threads\n";
}

void ThreadManager::workerThread() {
    while (true) {
        TaskEntry taskEntry;
        {
            std::unique_lock<std::mutex> lock(queueMutex);
            cv.wait(lock,
                    [this]() { return !taskQueue.empty() || !running.load(); });
            if (!running.load() && taskQueue.empty()) {
                std::cout << "Worker thread exiting\n";
                active_threads--;
                return;  // Завершаем работу, если нет задач и флаг running
                         // установлен в false
            }
            taskEntry = taskQueue.top();
            taskQueue.pop();
            tasks_in_queue--;
            // active_threads--;
            std::cout << "Task taken from queue, tasks_in_queue: "
                      << tasks_in_queue.load()
                      << ", active_threads: " << active_threads.load() << "\n";
        }
        if (!groupRunning.load()[taskEntry.groupID]) {
            std::cout << "Skipping task from group " << taskEntry.groupID
                      << "\n";
            continue;  // Пропускаем задачи из остановленных групп
        }
        try {
            (*taskEntry.task)();
        } catch (const std::exception& e) {
            std::cerr << "Task error: " << e.what() << "\n";
        }
        {
            std::lock_guard<std::mutex> lock(queueMutex);
            active_threads--;
            if (active_threads + tasks_in_queue == 0) {
                cv.notify_one();  // Все задачи выполнены
                std::cout << "All tasks completed\n";
            }
        }
    }
}

std::unordered_map<size_t, size_t> ThreadManager::waitForAll() {
    std::unique_lock<std::mutex> lock(queueMutex);
    cv.wait(lock, [this]() {
        return active_threads.load() + tasks_in_queue.load() == 0;
    });
    std::cout << "waitForAll completed\n";

    std::unordered_map<size_t, size_t> results;
    for (auto& [taskID, future] : taskResults) {
        results[taskID] = future.get();
    }
    taskResults.clear();
    return results;
}

void ThreadManager::waitForTask(size_t taskID) {
    if (taskResults.find(taskID) == taskResults.end()) {
        std::cerr << "Task ID " << taskID << " not found\n";
        return;
    }
    taskResults[taskID].wait();
    std::cout << "Task " << taskID << " completed\n";
}

void ThreadManager::startWorkerIfNecessary() {
    std::lock_guard<std::mutex> lock(queueMutex);
    if (active_threads.load() < maxThreads && tasks_in_queue.load() > 0) {
        threads.emplace_back(&ThreadManager::workerThread, this);
        active_threads++;
        std::cout << "Started new worker thread, active_threads: "
                  << active_threads.load() << "\n";
    }
}

size_t ThreadManager::getActive_threads() { return active_threads.load(); }
size_t ThreadManager::getTasks_in_queue() { return tasks_in_queue.load(); }