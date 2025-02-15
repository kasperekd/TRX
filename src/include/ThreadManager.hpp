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
    ~ThreadManager();

    template <typename Func, typename... Args>
    size_t addTask(Func&& func, Args&&... args,
                   TaskPriority priority = TaskPriority::Normal,
                   size_t groupID = 0);

    void stopAll();
    void stopGroup(size_t groupID);
    void resizeThreadPool(size_t newSize);
    std::unordered_map<size_t, size_t> waitForAll();
    void waitForTask(size_t taskID);

    size_t getActive_threads();
    size_t getTasks_in_queue();

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
    std::mutex resultMutex;
    std::unordered_map<size_t, std::future<size_t>> taskResults;
    std::atomic<size_t> nextTaskID;
};

template <typename Func, typename... Args>
size_t ThreadManager::addTask(Func&& func, Args&&... args,
                              TaskPriority priority, size_t groupID) {
    if (groupID >= MAX_THREAD_GROUP) {
        std::cerr << "Invalid group ID: " << groupID << std::endl;
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
        tasks_in_queue++;
        taskResults[taskID] = std::move(future);
    }
    cv.notify_one();
    startWorkerIfNecessary();
    return taskID;
}

#endif  // THREAD_MANAGER_HPP