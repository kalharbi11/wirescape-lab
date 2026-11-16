// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// Test-only frozen ABI1 bytes: generated once from actual passing legacy calls.
// CMake verifies source-archive and each per-case hash before writing these files.
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <sstream>
#include <string>
#include <vector>

#ifndef ABI1_FROZEN_DIR
#error "ABI1_FROZEN_DIR must name the verified build-local fixture directory"
#endif

inline std::filesystem::path abi1_frozen_path(const std::string& id,
                                             const char* extension) {
    VERIFY(!id.empty() && id.find('/') == std::string::npos &&
           id.find('\\') == std::string::npos && id.find("..") == std::string::npos);
    return std::filesystem::path(ABI1_FROZEN_DIR) / (id + extension);
}

inline std::vector<float> abi1_frozen_samples(const std::string& id) {
    const auto path = abi1_frozen_path(id, ".f32le");
    std::ifstream file(path, std::ios::binary | std::ios::ate);
    VERIFY(file);
    const std::streamoff length = file.tellg();
    VERIFY(length > 0 && length % 4 == 0 && length <= 1024 * 1024);
    std::vector<unsigned char> bytes(static_cast<size_t>(length));
    file.seekg(0);
    VERIFY(static_cast<bool>(file.read(reinterpret_cast<char*>(bytes.data()), length)));
    std::vector<float> samples(bytes.size() / 4);
    for(size_t i=0;i<samples.size();++i) {
        const unsigned char* p=bytes.data()+i*4;
        uint32_t bits=uint32_t(p[0])|(uint32_t(p[1])<<8)|
                      (uint32_t(p[2])<<16)|(uint32_t(p[3])<<24);
        std::memcpy(&samples[i],&bits,4);
    }
    return samples;
}

struct Abi1FrozenParam {
    uint32_t legacy_index=0;
    float minimum=0,maximum=0,initial=0;
};
struct Abi1FrozenDescriptor {
    std::string id;
    uint32_t input_count=0,output_count=0,parameter_count=0;
    std::vector<std::string> inputs,outputs;
    std::vector<Abi1FrozenParam> parameters;
};

inline Abi1FrozenDescriptor abi1_frozen_descriptor(const std::string& module) {
    std::ifstream file(abi1_frozen_path("utility_"+module, ".desc"));
    VERIFY(file);
    Abi1FrozenDescriptor d;
    std::string line;
    while(std::getline(file,line)) {
        if(line.empty())continue;
        std::istringstream row(line);
        std::string key;
        VERIFY(static_cast<bool>(std::getline(row,key,'\t')));
        if(key=="id") {
            VERIFY(static_cast<bool>(std::getline(row,d.id)) && !d.id.empty());
        } else if(key=="counts") {
            std::string a,b,c;
            VERIFY(static_cast<bool>(std::getline(row,a,'\t')) &&
                   static_cast<bool>(std::getline(row,b,'\t')) &&
                   static_cast<bool>(std::getline(row,c)));
            d.input_count=static_cast<uint32_t>(std::stoul(a));
            d.output_count=static_cast<uint32_t>(std::stoul(b));
            d.parameter_count=static_cast<uint32_t>(std::stoul(c));
        } else if(key=="input"||key=="output") {
            std::string pos,value;
            VERIFY(static_cast<bool>(std::getline(row,pos,'\t')) &&
                   static_cast<bool>(std::getline(row,value)));
            auto& list=(key=="input")?d.inputs:d.outputs;
            VERIFY(std::stoul(pos)==list.size());
            list.push_back(value);
        } else if(key=="param") {
            std::string pos,id,lo,hi,init;
            VERIFY(static_cast<bool>(std::getline(row,pos,'\t')) &&
                   static_cast<bool>(std::getline(row,id,'\t')) &&
                   static_cast<bool>(std::getline(row,lo,'\t')) &&
                   static_cast<bool>(std::getline(row,hi,'\t')) &&
                   static_cast<bool>(std::getline(row,init)));
            VERIFY(std::stoul(pos)==d.parameters.size());
            Abi1FrozenParam p;
            p.legacy_index=static_cast<uint32_t>(std::stoul(id));
            auto decode=[](const std::string& hex) {
                VERIFY(hex.size()==8);
                uint32_t bits=static_cast<uint32_t>(std::stoul(hex,nullptr,16));
                float value;std::memcpy(&value,&bits,4);return value;
            };
            p.minimum=decode(lo);p.maximum=decode(hi);p.initial=decode(init);
            d.parameters.push_back(p);
        } else {
            VERIFY(false);
        }
    }
    VERIFY(!d.id.empty() && d.inputs.size()==d.input_count &&
           d.outputs.size()==d.output_count &&
           d.parameters.size()==d.parameter_count);
    return d;
}
