// SPDX-License-Identifier: GPL-3.0-only
#include "wirescape_sdk.h"
#include "data_pack.h"
#include <cstdio>
#include <cstdlib>
#define CHECK(x) do { if (!(x)) { std::fprintf(stderr, "data pack line %d: %s\n", __LINE__, #x); std::abort(); } } while (0)

using nlohmann::json;
using namespace ws::data_layout;
#define ROW_FIELDS(X, S) \
 X(S, velocity, float, WS2_F_F32, "Velocity", ws::data_range(0,1,.5)) \
 X(S, note, uint8_t, WS2_F_U8, "Note", ws::data_range(0,127,60))
WS_DEFINE_DATA_STRUCT(RowData, ROW_FIELDS)
inline constexpr const char *modes[] = {"free", "sync"};
#define SLOT_FIELDS(X, S) \
 X(S, length, uint32_t, WS2_F_U32, "Length", ws::data_range(0,3,0)) \
 X(S, steps, RowData[3], WS2_F_RECORD, "Steps", ws::data_record(RowData_fields,0)) \
 X(S, gain, float, WS2_F_F32, "Gain", ws::data_range(0,1,.25)) \
 X(S, mode, uint32_t, WS2_F_ENUM, "Mode", ws::data_options(modes,1)) \
 X(S, enabled, uint8_t, WS2_F_BOOL, "Enabled", ws::data_range(0,1,1)) \
 X(S, title, char[8], WS2_F_TEXT, "Title", ws::DataFieldRules{}) \
 X(S, bins, int32_t[2], WS2_F_I32, "Bins", ws::data_range(-4,4,-1))
WS_DEFINE_DATA_STRUCT(SlotData, SLOT_FIELDS)

int main() {
    constexpr auto slot = ws::data_slot<SlotData>("settings","Settings",SlotData_fields);
    std::vector<uint8_t> out, second;
    std::vector<std::string> warnings;
    std::string error;
    auto pack = [&](const json &value, DataLoad policy = DataLoad::Edit) {
        return pack_data_slot(slot, value, policy, out, error, &warnings);
    };
    auto read = [&] {
        SlotData data{};
        CHECK(out.size() == sizeof(data));
        std::memcpy(&data, out.data(), sizeof(data));
        return data;
    };
    CHECK(pack(json::object()));
    auto d = read();
    CHECK(d.length == 0 && d.gain == .25f && d.mode == 1 && d.enabled == 1);
    CHECK(d.title[0] == 0 && d.bins[0] == -1 && d.bins[1] == -1);
    for (const auto &step : d.steps) CHECK(step.velocity == 0 && step.note == 0);
    const json valid = {{"steps", json::array({{{"velocity",.75},{"note",72}},{{"note",80}}})},
                        {"title","hello"},{"mode","free"},{"enabled",false},{"bins",json::array({-4,4})}};
    CHECK(pack(valid));
    d = read();
    CHECK(d.length == 2 && d.steps[0].velocity == .75f && d.steps[0].note == 72);
    CHECK(d.steps[1].velocity == .5f && d.steps[1].note == 80);
    CHECK(d.steps[2].velocity == 0 && d.steps[2].note == 0);
    CHECK(d.mode == 0 && d.enabled == 0 && std::strcmp(d.title,"hello") == 0);
    CHECK(d.bins[0] == -4 && d.bins[1] == 4);
    CHECK(pack_data_slot(slot,valid,DataLoad::Edit,second,error));
    CHECK(out == second);
    // Padding of a record is zero, not compiler-dependent garbage.
    for (size_t i = offsetof(RowData,note)+sizeof(uint8_t); i < sizeof(RowData); ++i)
        CHECK(out[offsetof(SlotData,steps)+i] == 0);
    const auto snapshot = out;
    auto refuse = [&](json bad, const char *field) {
        CHECK(!pack(bad));
        CHECK(error.find(field) != std::string::npos && out == snapshot);
    };
    refuse({{"gain",2}},"settings.gain");
    refuse({{"enabled",1}},"enabled");
    refuse({{"mode","bad"}},"mode");
    refuse({{"title","12345678"}},"title");
    refuse({{"title",std::string("a\0b",3)}},"title");
    refuse({{"title",std::string("\xc0\xaf",2)}},"title");
    refuse({{"length",2}},"length");
    refuse({{"bins",json::array({1})}},"bins");
    refuse({{"bins",json::array({1.5,2})}},"bins[0]");
    refuse({{"steps",json::array({{{"velocity",2}}})}},"steps[0].velocity");
    refuse({{"steps",json::array({json::object(),json::object(),json::object(),json::object()})}},"steps");
    refuse({{"unknown",1}},"unknown");
    const json stored = {{"steps",json::array({{{"velocity",.25},{"future",7}}})},{"unknown",42}};
    CHECK(pack(stored,DataLoad::StoredDocument));
    CHECK(warnings.size() == 2 && read().steps[0].velocity == .25f);
    CHECK(stored.contains("unknown") && stored["steps"][0].contains("future"));
    // A77: the optional callback sees canonical packed defaults, not authored JSON.
    // On cross-field refusal, neither prior bytes nor stored-field warnings change.
    const auto cross_field = +[](const ws2_data_slot &, const std::vector<uint8_t> &bytes, std::string &error) {
        SlotData packed{};
        std::memcpy(&packed, bytes.data(), sizeof(packed));
        if (packed.length && packed.steps[0].velocity < packed.gain) {
            error = "settings.steps[0].velocity: below gain";
            return false;
        }
        return true;
    };
    const auto saved = out;
    const auto saved_warnings = warnings;
    const json low = {{"steps", json::array({{{"velocity", .125}}})}, {"unknown", 1}};
    CHECK(!pack_data_slot(slot, low, DataLoad::StoredDocument, out, error, &warnings, cross_field));
    CHECK(error == "settings.steps[0].velocity: below gain");
    CHECK(out == saved && warnings == saved_warnings);
    CHECK(pack_data_slot(slot, valid, DataLoad::Edit, out, error, &warnings, cross_field));
    CHECK(read().steps[0].velocity == .75f);
    // Invalid field metadata is refused before any packing.
    auto fields = SlotData_fields;
    auto malformed = slot;
    malformed.fields = fields.data();
    fields[2].offset = fields[0].offset;
    CHECK(!pack_data_slot(malformed,json::object(),DataLoad::Edit,second,error));
    CHECK(error.find("gain") != std::string::npos);
    fields = SlotData_fields;
    fields[1].length_field = 2; // F32, not scalar U32.
    CHECK(!pack_data_slot(malformed,json::object(),DataLoad::Edit,second,error));
    CHECK(error.find("steps") != std::string::npos);
    std::puts("PASS E3a field tables, defaults, generic JSON packing, rejection and stored unknowns");
}
