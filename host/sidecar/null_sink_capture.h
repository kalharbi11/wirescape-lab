// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// --capture-null-sink <file> (T0.13a, proposals/0005 section 4, ENGINE_PROTOCOL section 9).
//
// File layout, all integers little-endian:
//   one or more segments; a segment starts each time the null-sink thread starts
//   (startup, setBufferFrames/setSampleRate, any quiescent restart) and is
//     40-byte header: magic "WSNSCAP1", u32 version=1, u32 header_bytes=40,
//                     u32 rate, u32 channels, u32 block, u32 segment index,
//                     u64 blocks (UINT64_MAX while the segment is still open)
//     followed by `blocks` rendered blocks, each block*channels float32
//     interleaved by frame (frame0 ch0..chN-1, frame1 ...).
// Only the null-sink thread writes after open(); the control thread opens
// before the thread starts and closes after it has joined. Nothing here is
// called from Engine::render or a device callback.
//
// <file>.marks (M0 r3 / R7, proposals/0005 section 4): one JSON line per handled
// command, {"re","type","ok","gen","b0","b1"}, written by the control thread only.
// b0/b1 are appended() read just before the command is applied and just after its
// reply is built. The sink thread's only part is one atomic increment per block.
#include <atomic>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>

namespace wirescape::sidecar {
class NullSinkCapture {
  public:
    static constexpr char kMagic[8] = {'W', 'S', 'N', 'S', 'C', 'A', 'P', '1'};
    static constexpr uint32_t kVersion = 1, kHeaderBytes = 40;
    static constexpr uint64_t kOpenSegment = UINT64_MAX;

    NullSinkCapture() = default;
    NullSinkCapture(const NullSinkCapture &) = delete;
    NullSinkCapture &operator=(const NullSinkCapture &) = delete;
    ~NullSinkCapture() { close(); }

    // Control thread, before any sink thread exists.
    bool open(const std::string &path) {
        close();
        file_ = std::fopen(path.c_str(), "wb");
        failed_ = false;
        segments_ = 0;
        blocks_.store(0, std::memory_order_relaxed);
        return file_ != nullptr;
    }
    bool enabled() const noexcept { return file_ != nullptr; }
    // Control thread, after the sink thread has joined.
    void close() noexcept {
        if (!file_) return;
        if (std::fflush(file_) != 0) failed_ = true;
        if (std::fclose(file_) != 0) failed_ = true;
        file_ = nullptr;
    }

    // Sink thread: start a segment. Its block count is patched in end().
    void begin(uint32_t rate, uint32_t channels, uint32_t block) noexcept {
        if (!file_ || failed_) return;
        segment_offset_ = tell();
        segment_blocks_ = 0;
        unsigned char header[kHeaderBytes];
        std::memcpy(header, kMagic, 8);
        put32(header + 8, kVersion);
        put32(header + 12, kHeaderBytes);
        put32(header + 16, rate);
        put32(header + 20, channels);
        put32(header + 24, block);
        put32(header + 28, segments_);
        put64(header + 32, kOpenSegment);
        if (segment_offset_ < 0 || std::fwrite(header, 1, sizeof header, file_) != sizeof header) {
            failed_ = true;
            return;
        }
        open_segment_ = true;
        ++segments_;
    }
    // Sink thread: append one rendered block. `scratch` holds frames*channels floats.
    void append(const float *const *rows, uint32_t channels, uint32_t frames, float *scratch) noexcept {
        if (!file_ || failed_ || !open_segment_) return;
        for (uint32_t i = 0; i < frames; ++i)
            for (uint32_t c = 0; c < channels; ++c) scratch[size_t(i) * channels + c] = rows[c][i];
        const size_t count = size_t(frames) * channels;
        if (std::fwrite(scratch, sizeof(float), count, file_) != count) {
            failed_ = true;
            return;
        }
        ++segment_blocks_;
        blocks_.fetch_add(1, std::memory_order_release); // after the block is appended
    }
    // Sink thread: close the segment by recording the number of complete blocks.
    void end() noexcept {
        if (!file_ || !open_segment_) return;
        open_segment_ = false;
        unsigned char count[8];
        put64(count, segment_blocks_);
        const auto resume = tell();
        if (resume < 0 || seek(segment_offset_ + 32) != 0 || std::fwrite(count, 1, 8, file_) != 8 ||
            seek(resume) != 0 || std::fflush(file_) != 0)
            failed_ = true;
    }

    // Read on the control thread only after the sink thread has joined.
    bool failed() const noexcept { return failed_; }
    uint32_t segments() const noexcept { return segments_; }
    uint64_t blocks() const noexcept { return appended(); }
    // Any thread: total blocks appended across all segments so far.
    uint64_t appended() const noexcept { return blocks_.load(std::memory_order_acquire); }

  private:
    std::FILE *file_ = nullptr;
    bool failed_ = false, open_segment_ = false;
    uint32_t segments_ = 0;
    std::atomic<uint64_t> blocks_{0};
    uint64_t segment_blocks_ = 0;
    int64_t segment_offset_ = 0;

    static void put32(unsigned char *p, uint32_t v) noexcept {
        for (int i = 0; i < 4; ++i) p[i] = static_cast<unsigned char>(v >> (8 * i));
    }
    static void put64(unsigned char *p, uint64_t v) noexcept {
        for (int i = 0; i < 8; ++i) p[i] = static_cast<unsigned char>(v >> (8 * i));
    }
    int64_t tell() noexcept {
#ifdef _WIN32
        return _ftelli64(file_);
#else
        return static_cast<int64_t>(ftello(file_));
#endif
    }
    int seek(int64_t at) noexcept {
#ifdef _WIN32
        return _fseeki64(file_, at, SEEK_SET);
#else
        return fseeko(file_, static_cast<off_t>(at), SEEK_SET);
#endif
    }
};

// Control thread only: the <capture>.marks companion file.
class CaptureMarks {
  public:
    CaptureMarks() = default;
    CaptureMarks(const CaptureMarks &) = delete;
    CaptureMarks &operator=(const CaptureMarks &) = delete;
    ~CaptureMarks() { close(); }
    bool open(const std::string &path) {
        close();
        file_ = std::fopen(path.c_str(), "wb");
        return file_ != nullptr;
    }
    bool enabled() const noexcept { return file_ != nullptr; }
    // One complete line, flushed so a killed engine still leaves every handled mark.
    void write(const std::string &line) noexcept {
        if (!file_ || failed_) return;
        if (std::fwrite(line.data(), 1, line.size(), file_) != line.size() || std::fputc('\n', file_) == EOF ||
            std::fflush(file_) != 0)
            failed_ = true;
    }
    bool failed() const noexcept { return failed_; }
    void close() noexcept {
        if (!file_) return;
        if (std::fclose(file_) != 0) failed_ = true;
        file_ = nullptr;
    }

  private:
    std::FILE *file_ = nullptr;
    bool failed_ = false;
};
} // namespace wirescape::sidecar
