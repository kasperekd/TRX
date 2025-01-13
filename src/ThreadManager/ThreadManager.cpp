#include "ThreadManager.hpp"

ThreadManager::ThreadManager(size_t maxThreads)
    : running(true),
      maxThreads(maxThreads),
      groupRunning(std::bitset<MAX_THREAD_GROUP>().set()),
      tasks_in_queue(0) {
    threads.reserve(maxThreads);
    for (size_t i = 0; i < maxThreads; ++i) {
        threads.emplace_back(&ThreadManager::workerThread, this);
    }
}

ThreadManager::~ThreadManager() { stopAll(); }

void ThreadManager::addTask(const Task& task, TaskPriority priority,
                            size_t groupID) {
    if (groupID >= MAX_THREAD_GROUP) {
        std::cerr << "Invalid group ID: " << groupID << std::endl;
        return;
    }
    {
        std::lock_guard<std::mutex> lock(queueMutex);
        taskQueue.push(TaskEntry{task, priority, groupID});
        tasks_in_queue++;
    }
    cv.notify_one();
}

void ThreadManager::stopAll() {
    {
        std::lock_guard<std::mutex> lock(queueMutex);
        running.store(false);
    }
    cv.notify_all();

    for (auto& thread : threads) {
        if (thread.joinable()) {
            thread.join();
        }
    }
    threads.clear();
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
        // std::priority_queue<TaskEntry> newQueue;
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
}

void ThreadManager::resizeThreadPool(size_t newSize) {
    if (newSize < maxThreads) {
        size_t threadsToStop = maxThreads - newSize;

        {
            std::lock_guard<std::mutex> lock(queueMutex);
            running.store(false);
        }
        cv.notify_all();

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
        }
        cv.notify_all();
    } else {
        size_t threadsToAdd = newSize - maxThreads;
        for (size_t i = 0; i < threadsToAdd; ++i) {
            threads.emplace_back(&ThreadManager::workerThread, this);
        }
        maxThreads = newSize;
    }
}

void ThreadManager::workerThread() {
    while (running.load()) {
        TaskEntry taskEntry;
        {
            std::unique_lock<std::mutex> lock(queueMutex);
            cv.wait(lock,
                    [this]() { return !taskQueue.empty() || !running.load(); });

            if (!running.load() && taskQueue.empty()) {
                return;
            }

            taskEntry = taskQueue.top();
            taskQueue.pop();
            tasks_in_queue--;

            if (tasks_in_queue == 0) {
                cv.notify_one();
            }
        }

        if (!groupRunning.load()[taskEntry.groupID]) {
            continue;
        }

        try {
            taskEntry.task();
        } catch (const std::exception& e) {
            std::cerr << "Task error: " << e.what() << std::endl;
        }
    }
}

void ThreadManager::waitForAll() {
    std::unique_lock<std::mutex> lock(queueMutex);
    cv.wait(lock, [this]() { return tasks_in_queue == 0; });
}