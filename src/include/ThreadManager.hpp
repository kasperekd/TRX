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
#include <type_traits>  // Для std::result_of
#include <vector>

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
        bool operator>(const TaskEntry& other) const {
            return priority > other.priority;
        }
    };

    ThreadManager(size_t maxThreads = std::thread::hardware_concurrency(),
                  bool roundRobin = false);
    ~ThreadManager();

    template <typename Func, typename... Args>
    std::future<typename std::result_of<Func(Args...)>::type> addTask(
        Func&& func, Args&&... args,
        TaskPriority priority = TaskPriority::Normal, size_t groupID = 0);

    void stopAll();
    void stopGroup(size_t groupID);
    void resizeThreadPool(size_t newSize);
    void waitForAll();

   private:
    void workerThread();
    void startWorkerIfNecessary();
    std::atomic<bool> running;
    size_t maxThreads;
    std::vector<std::thread> threads;
    std::priority_queue<TaskEntry, std::vector<TaskEntry>,
                        std::greater<TaskEntry>>
        taskQueue;
    std::atomic<std::bitset<MAX_THREAD_GROUP>> groupRunning;
    std::mutex queueMutex;
    std::condition_variable cv;
    std::atomic<size_t> tasks_in_queue;
    std::atomic<size_t> active_threads;
    bool roundRobin;
};

template <typename Func, typename... Args>
std::future<typename std::result_of<Func(Args...)>::type>
ThreadManager::addTask(Func&& func, Args&&... args, TaskPriority priority,
                       size_t groupID) {
    if (groupID >= MAX_THREAD_GROUP) {
        std::cerr << "Invalid group ID: " << groupID << std::endl;
        return std::future<typename std::result_of<Func(Args...)>::type>();
    }

    using ReturnType = typename std::result_of<Func(Args...)>::type;
    auto packagedTask = std::make_shared<std::packaged_task<ReturnType()>>(
        std::bind(std::forward<Func>(func), std::forward<Args>(args)...));
    std::future<ReturnType> future = packagedTask->get_future();

    {
        std::lock_guard<std::mutex> lock(queueMutex);
        taskQueue.push(TaskEntry{packagedTask, priority, groupID});
        tasks_in_queue++;
    }
    cv.notify_one();

    startWorkerIfNecessary();

    return future;
}

#endif  // THREAD_MANAGER_HPP