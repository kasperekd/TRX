#ifndef RINGBUFFER_HPP
#define RINGBUFFER_HPP

#include <atomic>
#include <stdexcept>
#include <vector>

// FIXME: Обязательно убрать использование vector !
template <typename T>
class RingBuffer {
   public:
    explicit RingBuffer(size_t capacity)
        : buffer_(capacity),
          head_(0),
          tail_(0),
          size_(0),
          capacity_(capacity) {}

    bool push(const T& value) {
        if (size_.load(std::memory_order_acquire) == capacity_) {
            return false;  // Буфер полон
        }
        buffer_[head_] = value;
        head_ = (head_ + 1) % capacity_;
        size_.fetch_add(1, std::memory_order_release);
        return true;
    }

    bool pop(T& value) {
        if (size_.load(std::memory_order_acquire) == 0) {
            return false;  // Буфер пуст
        }
        value = buffer_[tail_];
        tail_ = (tail_ + 1) % capacity_;
        size_.fetch_sub(1, std::memory_order_release);
        return true;
    }

    size_t size() const { return size_.load(std::memory_order_acquire); }
    size_t capacity() const { return capacity_; }

   private:
    std::vector<T> buffer_;
    std::atomic<size_t> head_;
    std::atomic<size_t> tail_;
    std::atomic<size_t> size_;
    size_t capacity_;
};

#endif  // RINGBUFFER_HPP