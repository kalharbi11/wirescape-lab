// SPDX-License-Identifier: GPL-3.0-only
#include "app_engine.h"
#include <nlohmann/json.hpp>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>

namespace {
using Json = nlohmann::json;

void insert_unique(Json &map, const char *id, Json value) {
    if (!id || !*id || map.contains(id))
        throw std::runtime_error("missing or duplicate descriptor ID");
    map[id] = std::move(value);
}

Json describe(const ws2_descriptor &d) {
    Json inputs = Json::object(), outputs = Json::object();
    Json parameters = Json::object(), ports = Json::array(), details = Json::array();
    for (bool output : {false, true}) {
        const auto *p = output ? d.outputs : d.inputs;
        const auto count = output ? d.output_count : d.input_count;
        for (uint32_t i = 0; i < count; ++i) {
            const auto &port = p[i];
            if (port.kind != WS2_SIGNAL && port.kind != WS2_EVENT)
                throw std::runtime_error("unknown port kind");
            const char *kind = port.kind == WS2_EVENT ? "event" : "signal";
            insert_unique(output ? outputs : inputs, port.id, kind);
            ports.push_back({{"id", port.id}, {"name", port.name},
                             {"direction", output ? "output" : "input"},
                             {"kind", kind}, {"hint", port.hint}, {"poly", port.poly},
                             {"stereo_pair", port.stereo_pair ? Json(port.stereo_pair) : Json(nullptr)},
                             {"unpatched_value", port.unpatched_value}});
        }
    }
    for (uint32_t i = 0; i < d.param_count; ++i) {
        const auto &p = d.params[i];
        insert_unique(parameters, p.id, p.legacy_index);
        Json choices = Json::array();
        for (uint32_t j = 0; j < p.option_count; ++j)
            choices.push_back(p.options[j]);
        details.push_back({{"id", p.id}, {"name", p.name}, {"unit", p.unit ? p.unit : ""},
                           {"minimum", p.minimum}, {"maximum", p.maximum}, {"default", p.initial},
                           {"legacy_index", p.legacy_index}, {"taper", p.taper}, {"curve", p.curve},
                           {"step", p.step}, {"flags", p.flags}, {"decimals", p.decimals},
                           {"choices", choices}});
    }
    return {{"id", d.id}, {"name", d.name}, {"abi_version", d.abi_version},
            {"version", d.version}, {"inputs", inputs}, {"outputs", outputs},
            {"parameters", parameters}, {"ports", ports}, {"parameter_details", details}};
}
} // namespace

int main() {
    try {
        // The native app catalogue is constructed without preparing a graph or
        // opening audio/MIDI devices, sockets, or module instances.
        const wirescape::engine2::Config config{};
        std::unique_ptr<AppEngine, decltype(&app_engine_destroy)> engine(
            app_engine_create(&config), app_engine_destroy);
        if (!engine) throw std::runtime_error("cannot construct built-in catalogue");
        Json modules = Json::array(), seen = Json::object();
        for (uint32_t i = 0; i < app_engine_module_count(engine.get()); ++i) {
            const auto *d = app_engine_module(engine.get(), i);
            if (!d) throw std::runtime_error("null built-in descriptor");
            insert_unique(seen, d->id, true);
            modules.push_back(describe(*d));
        }
        std::cout << Json{{"modules", modules}}.dump(2) << '\n';
        return std::cout ? 0 : 1;
    } catch (const std::exception &e) {
        std::cerr << "wire-describe: " << e.what() << '\n';
        return 1;
    }
}
