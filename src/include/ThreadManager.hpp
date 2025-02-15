#ifndef THREAD_MANAGER_HPP
#define THREAD_MANAGER_HPP

#include <atomic>
#include <bitset>
#include <condition_variable>
#include <functional>
#include <future>
#include <iostream>
#include <memory>
#include <mutex>
#include <queue>
#include <thread>
#include <type_traits>
#include <unordered_map>
#include <vector>

// #define DEBUG
#ifdef DEBUG
#define LOG(msg) std::cout << msg << std::endl
#else
#define LOG(msg) ((void)0)
#endif

#define ERROR(msg) std::cerr << "Error: " << msg << std::endl

#ifndef MAX_THREAD_GROUP
#define MAX_THREAD_GROUP 100
#endif

class ThreadManager {
   public:
    using Task = std::function<void()>;
    enum class TaskPriority { High, Normal, Low };
    struct TaskEntry {
        std::shared_ptr<std::packaged_task<size_t()>> task;
        TaskPriority priority;
        size_t groupID;
        size_t taskID;
        bool operator>(const TaskEntry& other) const {
            return priority > other.priority;
        }
    };

    ThreadManager(size_t maxThreads = std::thread::hardware_concurrency(),
                  bool roundRobin = false);
    ThreadManager();
    template <typename Func, typename... Args>
    size_t addTask(Func&& func, Args&&... args,
                   TaskPriority priority = TaskPriority::Normal,
                   size_t groupID = 0);
    void stopAll();
    void stopGroup(size_t groupID);
    void resizeThreadPool(size_t newSize);
    std::unordered_map<size_t, size_t> waitForAll();
    size_t waitForTask(size_t taskID);
    size_t getActiveThreads();
    size_t getTasksInQueue();
    size_t getBusyWorkers();

   private:
    void workerThread();
    void startWorkerIfNecessary();

    // container
    std::vector<std::thread> threads;
    std::priority_queue<TaskEntry, std::vector<TaskEntry>,
                        std::greater<TaskEntry>>
        taskQueue;
    std::unordered_map<size_t, std::future<size_t>> taskResults;

    // atomic
    std::atomic<bool> running;
    std::atomic<size_t> tasksInQueue;
    std::atomic<size_t> activeThreads;
    std::atomic<size_t> busyWorkers;
    std::atomic<size_t> nextTaskID;
    std::atomic<std::bitset<MAX_THREAD_GROUP>> groupRunning;

    // pupupu
    size_t maxThreads;
    bool roundRobin;

    // sync
    std::mutex queueMutex;
    std::mutex resultMutex;
    std::condition_variable cv;
};

template <typename Func, typename... Args>
size_t ThreadManager::addTask(Func&& func, Args&&... args,
                              TaskPriority priority, size_t groupID) {
    if (groupID >= MAX_THREAD_GROUP) {
        ERROR("Invalid group ID: " << groupID);
        return 0;
    }
    using ReturnType = typename std::result_of<Func(Args...)>::type;
    auto packagedTask = std::make_shared<std::packaged_task<ReturnType()>>(
        std::bind(std::forward<Func>(func), std::forward<Args>(args)...));
    std::future<ReturnType> future = packagedTask->get_future();
    size_t taskID = nextTaskID++;
    {
        std::lock_guard<std::mutex> lock(queueMutex);
        taskQueue.push(TaskEntry{packagedTask, priority, groupID, taskID});
        tasksInQueue++;
        taskResults[taskID] = std::move(future);
    }
    cv.notify_one();
    startWorkerIfNecessary();
    LOG("Task added with ID: " << taskID
                               << ", Priority: " << static_cast<int>(priority)
                               << ", Group ID: " << groupID);
    return taskID;
}

#endif  // THREAD_MANAGER_HPP