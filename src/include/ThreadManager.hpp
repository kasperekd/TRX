#ifndef THREAD_MANAGER_HPP
#define THREAD_MANAGER_HPP

#include <atomic>
#include <bitset>
#include <condition_variable>
#include <functional>
#include <iostream>
#include <mutex>
#include <queue>
#include <thread>
#include <vector>

#ifndef MAX_THREAD_GROUP
#define MAX_THREAD_GROUP 100
#endif

// TODO: Добавить возможность ожидать выполнение конкретной задачи и/или группы
// задач

class ThreadManager {
   public:
    using Task = std::function<void()>;

    enum class TaskPriority { High, Normal, Low };

    struct TaskEntry {
        Task task;
        TaskPriority priority;
        size_t groupID;

        bool operator>(const TaskEntry& other) const {
            return priority > other.priority;
        }
    };

    ThreadManager(size_t maxThreads = std::thread::hardware_concurrency());
    ~ThreadManager();

    void addTask(const Task& task, TaskPriority priority = TaskPriority::Normal,
                 size_t groupID = 0);
    void stopAll();
    void stopGroup(size_t groupID);
    void resizeThreadPool(size_t newSize);

    void waitForAll();

   private:
    void workerThread();

    std::atomic<bool> running;
    size_t maxThreads;

    std::vector<std::thread> threads;
    // std::priority_queue<TaskEntry> taskQueue;
    std::priority_queue<TaskEntry, std::vector<TaskEntry>,
                        std::greater<TaskEntry>>
        taskQueue;
    std::atomic<std::bitset<MAX_THREAD_GROUP>> groupRunning;

    std::mutex queueMutex;
    std::condition_variable cv;
    std::atomic<size_t> tasks_in_queue;
};

#endif  // THREAD_MANAGER_HPP