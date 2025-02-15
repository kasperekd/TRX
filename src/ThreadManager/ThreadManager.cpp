#include "ThreadManager.hpp"

ThreadManager::ThreadManager(size_t maxThreads, bool roundRobin)
    : running(true),
      tasksInQueue(0),
      activeThreads(0),
      busyWorkers(0),
      nextTaskID(1),
      groupRunning(std::bitset<MAX_THREAD_GROUP>().set()),
      maxThreads(maxThreads),
      roundRobin(roundRobin) {
    LOG("ThreadManager started with max " << maxThreads << " threads");
}

ThreadManager::ThreadManager() { stopAll(); }

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
    LOG("ThreadManager stopped");
}

void ThreadManager::stopGroup(size_t groupID) {
    if (groupID >= MAX_THREAD_GROUP) {
        ERROR("Invalid group ID: " << groupID);
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
    LOG("Group " << groupID << " stopped");
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
    } else {
        maxThreads = newSize;
    }
    {
        std::lock_guard<std::mutex> lock(queueMutex);
        running.store(true);
        cv.notify_all();  // Уведомляем новые потоки о начале работы
    }
    LOG("Thread pool resized to " << maxThreads << " threads");
}

void ThreadManager::workerThread() {
    while (true) {
        TaskEntry taskEntry;
        {
            std::unique_lock<std::mutex> lock(queueMutex);
            cv.wait(lock,
                    [this] { return !taskQueue.empty() || !running.load(); });
            if (!running.load() && taskQueue.empty()) {
                LOG("Worker thread exiting");
                activeThreads--;
                return;  // Завершаем работу, если нет задач и флаг running
                         // установлен в false
            }
            taskEntry = taskQueue.top();
            taskQueue.pop();
            tasksInQueue--;
            busyWorkers++;
            LOG("Task taken from queue, tasks_in_queue: "
                << tasksInQueue.load()
                << ", busy_workers: " << busyWorkers.load());
        }
        if (!groupRunning.load()[taskEntry.groupID]) {
            LOG("Skipping task from group " << taskEntry.groupID);
            {
                std::lock_guard<std::mutex> lock(queueMutex);
                busyWorkers--;
            }
            continue;  // Пропускаем задачи из остановленных групп
        }
        try {
            (*taskEntry.task)();
        } catch (const std::exception& e) {
            ERROR("Task error: " << e.what());
        }
        {
            std::lock_guard<std::mutex> lock(queueMutex);
            busyWorkers--;
            if (busyWorkers.load() + tasksInQueue.load() == 0) {
                cv.notify_one();  // Все задачи выполнены
                LOG("All tasks completed");
            }
        }
    }
}

std::unordered_map<size_t, size_t> ThreadManager::waitForAll() {
    std::unique_lock<std::mutex> lock(queueMutex);
    cv.wait(lock,
            [this] { return (busyWorkers.load() + tasksInQueue.load()) == 0; });
    LOG("waitForAll completed");
    std::unordered_map<size_t, size_t> results;
    for (auto& [taskID, future] : taskResults) {
        results[taskID] = future.get();
    }
    taskResults.clear();
    return results;
}

size_t ThreadManager::waitForTask(size_t taskID) {
    std::future<size_t> future;
    {
        std::lock_guard<std::mutex> lock(resultMutex);
        if (taskResults.find(taskID) == taskResults.end()) {
            ERROR("Task ID " << taskID << " not found");
            return 0;
        }
        future = std::move(taskResults[taskID]);
        taskResults.erase(taskID);
    }
    future.wait();
    LOG("Task " << taskID
                << " completed tasks_in_queue: " << tasksInQueue.load()
                << ", active_threads: " << activeThreads.load()
                << ", BusyWorkers: " << getBusyWorkers());
    return future.get();
}

void ThreadManager::startWorkerIfNecessary() {
    std::lock_guard<std::mutex> lock(queueMutex);
    if (activeThreads.load() < maxThreads && tasksInQueue.load() > 0) {
        threads.emplace_back(&ThreadManager::workerThread, this);
        activeThreads++;
        LOG("Started new worker thread, active_threads: "
            << activeThreads.load());
    }
}

size_t ThreadManager::getActiveThreads() { return activeThreads.load(); }
size_t ThreadManager::getTasksInQueue() { return tasksInQueue.load(); }
size_t ThreadManager::getBusyWorkers() { return busyWorkers.load(); }