// SPDX-License-Identifier: GPL-3.0-only
#pragma once
#include "wirescape_sdk.h"
#include "data_layout.h"
#include <algorithm>
#include <atomic>
#include <deque>
#include <cmath>
#include <cstring>
#include <limits>
#include <memory>
#include <new>
#include <string>
#include <vector>

namespace wirescape::engine2 {
struct DataBlockDelete {
    void operator()(uint8_t *p) const noexcept { ::operator delete(p, std::align_val_t(16)); }
};
using DataBlock = std::unique_ptr<uint8_t, DataBlockDelete>;
inline DataBlock allocate_data_block(uint32_t bytes) {
    DataBlock block(static_cast<uint8_t *>(::operator new(bytes, std::align_val_t(16))));
    std::memset(block.get(), 0, bytes);
    return block;
}
// Control-owned version history. Render borrows pointers only, and publishes
// acknowledgements after it has stopped using the preceding block (ER2).
struct DataVersion {
    uint32_t serial;
    DataBlock bytes;
};
struct DataSlotStorage {
    uint32_t size;
    bool initial_authored = false; // candidate installed a packed document block before prepare
    std::deque<DataVersion> versions;
    // Only set after a quiescent reset has discarded every queued packet.
    uint32_t canceled_through = 0;
    explicit DataSlotStorage(uint32_t bytes) : size(bytes) {}
    template<class IsLive>
    void reclaim(uint32_t oldest, IsLive is_live) noexcept {
        while (versions.size() > 1 && versions.front().serial < oldest)
            versions.pop_front();
        if (!canceled_through) return;
        // A canceled, never-referenced version has no ring reader left.
        // Keep every acknowledged version and the last authored block.
        // Reclamation is deferred to the control owner, never reset/render.
        for (auto it = versions.begin(); it != versions.end();) {
            if (it->serial == versions.back().serial || it->serial > canceled_through) break;
            if (!is_live(it->serial)) it = versions.erase(it);
            else ++it;
        }
        canceled_through = 0;
    }
};
struct InstanceData {
    std::vector<std::shared_ptr<DataSlotStorage>> owners; // control-only
    std::vector<ws2_data> view; // immutable shape, render-owned values after publication
    std::unique_ptr<std::atomic<uint32_t>[]> adopted;
    void init_views() {
        view.clear();
        view.reserve(owners.size());
        if (!owners.empty()) adopted = std::make_unique<std::atomic<uint32_t>[]>(owners.size());
        for (uint32_t i = 0; i < owners.size(); ++i) {
            const auto &slot = *owners[i];
            const auto &v = slot.versions.back();
            view.push_back({sizeof(ws2_data), v.bytes.get(), slot.size, v.serial});
            adopted[i].store(v.serial, std::memory_order_relaxed);
        }
    }
    // The bindings are immutable while an instance is visible to render.
    // Pointer comparison does not modify a reference count.
    bool shares_slot(const InstanceData &other, uint32_t slot) const noexcept {
        return slot < owners.size() && slot < other.owners.size() &&
               owners[slot].get() == other.owners[slot].get();
    }
    void apply(uint32_t slot, const void *bytes, uint32_t serial) noexcept {
        auto &v = view[slot];
        if (serial <= v.serial) return;
        v.data = bytes;
        v.serial = serial;
        adopted[slot].store(serial, std::memory_order_release);
    }
};
static_assert(std::atomic<uint32_t>::is_always_lock_free, "Data acknowledgement must be lock-free");

inline bool initialize_data_slots(const ws2_descriptor &d, InstanceData &data, std::string &error) {
    if (d.struct_size < offsetof(ws2_descriptor, data_slot_count) + sizeof(d.data_slot_count) ||
        !d.data_slot_count) return true;
    if (d.data_slot_count > WS2_MAX_DATA_SLOTS ||
        d.struct_size < offsetof(ws2_descriptor, data_slots) + sizeof(d.data_slots) || !d.data_slots) {
        error = "Invalid ABI2 data slot table";
        return false;
    }
    for (uint32_t i = 0; i < d.data_slot_count; ++i) {
        const auto &s = d.data_slots[i];
        if (s.struct_size < sizeof(ws2_data_slot)) { error = "Short data slot descriptor"; return false; }
        const std::string name = s.id ? s.id : "(null)";
        if (!ws::data_layout::data_id_valid(s.id) || !s.name || !s.bytes || s.bytes > WS2_MAX_DATA_BYTES || s.flags) {
            error = name + ": invalid data slot"; return false;
        }
        for (uint32_t j = 0; j < i; ++j)
            if (!std::strcmp(d.data_slots[j].id, s.id)) { error = name + ": duplicate data slot"; return false; }
        uint32_t alignment = 1;
        if (!ws::data_layout::validate_data_fields(s.fields, s.field_count, s.bytes, false, name, error, alignment)) return false;
        auto block = allocate_data_block(s.bytes);
        ws::data_layout::pack_data_defaults(s.fields, s.field_count, block.get());
        auto owner = std::make_shared<DataSlotStorage>(s.bytes);
        owner->versions.push_back({1, std::move(block)});
        data.owners.push_back(std::move(owner));
    }
    data.init_views();
    return true;
}
} // namespace wirescape::engine2
