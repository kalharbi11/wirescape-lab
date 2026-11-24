// SPDX-License-Identifier: GPL-3.0-only
#include "impl.h"

namespace wirescape::engine2 {
Engine::Engine(Config config) : p_(std::make_unique<Impl>(config)) {}
Engine::~Engine() = default;

const std::string &Engine::error() const { return p_->error; }
const ws2_descriptor *Engine::descriptor(uint32_t node) const {
    auto *n = p_->find(node);
    return n ? n->instance.d : nullptr;
}
uint32_t Engine::output_channels(uint32_t node, uint32_t port) const {
    auto *n = p_->find(node);
    return n && port < n->instance.global_out.size() ? n->instance.global_out[port].channels : 0;
}
bool Engine::output_constant(uint32_t node, uint32_t port) const {
    auto *n = p_->find(node);
    return n && port < n->instance.global_out.size() && (n->instance.global_out[port].flags & WS2_CONSTANT);
}
float Engine::output_sample(uint32_t node, uint32_t port, uint32_t channel, uint32_t frame) const {
    auto *n = p_->find(node);
    if (!n || port >= n->instance.global_out.size()) return 0;
    auto &b = n->instance.global_out[port];
    return channel < b.channels && frame < p_->cfg.max_block ? b.data[channel][(b.flags & WS2_CONSTANT) ? 0 : frame]
                                                             : 0;
}
uint32_t Engine::feedback_edges() const { return p_->feedback_count; }

uint32_t Engine::latency_frames(uint32_t bus) const { return bus < p_->bus_latency.size() ? p_->bus_latency[bus] : 0; }
std::vector<FeedbackLoop> Engine::feedback_loops() const {
    std::vector<FeedbackLoop> result;
    for (auto &component : p_->components)
        if (component.loop) {
            FeedbackLoop loop;
            loop.delay_frames = p_->cfg.feedback_block;
            for (auto *n : component.nodes) loop.nodes.push_back(n->instance.id);
            std::sort(loop.nodes.begin(), loop.nodes.end());
            result.push_back(std::move(loop));
        }
    return result;
}

uint32_t Engine::dropped_connections() const { return p_->dropped_connections; }

} // namespace wirescape::engine2
