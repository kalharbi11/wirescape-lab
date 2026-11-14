// SPDX-License-Identifier: GPL-3.0-only
// Explicitly owner-authorized Windows WASAPI process-tree loopback for the sidecar.
// This executable is never run from CI, unit tests, or a dry-run.
#define NOMINMAX
#include <windows.h>
#include <audioclient.h>
#include <audioclientactivationparams.h>
#include <mmdeviceapi.h>
#include <mmreg.h>
#include <wrl.h>
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

using Microsoft::WRL::ComPtr;
namespace {
void check(HRESULT h, const char* op) {
    if (FAILED(h)) throw std::runtime_error(std::string(op) + ": HRESULT " + std::to_string(static_cast<unsigned long>(h)));
}
struct Apartment {
    Apartment(){check(CoInitializeEx(nullptr, COINIT_MULTITHREADED),"CoInitializeEx");}
    ~Apartment(){CoUninitialize();}
};
struct Capture {
    ComPtr<IAudioClient> client;
    bool started=false;
    ~Capture(){if(started) client->Stop();}
};
struct Activator final : Microsoft::WRL::RuntimeClass<
    Microsoft::WRL::RuntimeClassFlags<Microsoft::WRL::ClassicCom>,
    Microsoft::WRL::FtmBase, IActivateAudioInterfaceCompletionHandler> {
    AUDIOCLIENT_ACTIVATION_PARAMS config{};
    PROPVARIANT params{};
    HANDLE ready=CreateEventW(nullptr,FALSE,FALSE,nullptr);
    HRESULT code=E_PENDING;
    ComPtr<IAudioClient> client;
    ~Activator(){if(ready) CloseHandle(ready);}
    HRESULT STDMETHODCALLTYPE ActivateCompleted(IActivateAudioInterfaceAsyncOperation* operation) override {
        HRESULT hr=E_FAIL;
        ComPtr<IUnknown> unk;
        code=operation->GetActivateResult(&hr,&unk);
        if (SUCCEEDED(code)) code=hr;
        if (SUCCEEDED(code)) code=unk.As(&client);
        SetEvent(ready);
        return S_OK;
    }
};
ComPtr<IAudioClient> capture_client(DWORD target) {
    auto handler=Microsoft::WRL::Make<Activator>();
    if (!handler || !handler->ready) throw std::runtime_error("activation setup failure");
    handler->config.ActivationType=AUDIOCLIENT_ACTIVATION_TYPE_PROCESS_LOOPBACK;
    handler->config.ProcessLoopbackParams.TargetProcessId=target;
    handler->config.ProcessLoopbackParams.ProcessLoopbackMode=PROCESS_LOOPBACK_MODE_INCLUDE_TARGET_PROCESS_TREE;
    handler->params.vt=VT_BLOB;
    handler->params.blob.cbSize=sizeof(handler->config);
    handler->params.blob.pBlobData=reinterpret_cast<BYTE*>(&handler->config);
    ComPtr<IActivateAudioInterfaceAsyncOperation> op;
    check(ActivateAudioInterfaceAsync(VIRTUAL_AUDIO_DEVICE_PROCESS_LOOPBACK,__uuidof(IAudioClient),
        &handler->params,handler.Get(),&op),"ActivateAudioInterfaceAsync (Windows build 20348+)");
    if (WaitForSingleObject(handler->ready,5000)!=WAIT_OBJECT_0)
        throw std::runtime_error("loopback activation timeout");
    check(handler->code,"ActivateCompleted");
    return handler->client;
}
void put16(std::ofstream& f,uint16_t n) {
    f.put(char(n&255));f.put(char((n>>8)&255));
}
void put32(std::ofstream& f,uint32_t n) {
    put16(f,uint16_t(n));put16(f,uint16_t(n>>16));
}
void header(std::ofstream& f,uint32_t rate,uint32_t bytes) {
    f.seekp(0);
    f.write("RIFF",4);put32(f,36+bytes);
    f.write("WAVEfmt ",8);put32(f,16);
    put16(f,3);put16(f,2);put32(f,rate);
    put32(f,rate*8);put16(f,8);put16(f,32);
    f.write("data",4);put32(f,bytes);
}
// Python's stdin pipe is left open until recording stops; EOF is a clean stop request.
bool stop_requested(HANDLE input) {
    if (!input || input==INVALID_HANDLE_VALUE || GetFileType(input)!=FILE_TYPE_PIPE) return false;
    DWORD available=0;
    if (PeekNamedPipe(input,nullptr,0,nullptr,&available,nullptr)) {
        if (available) {
            char byte;
            DWORD taken=0;
            ReadFile(input,&byte,1,&taken,nullptr);
            return true;
        }
        return false;
    }
    DWORD error=GetLastError();
    if (error==ERROR_BROKEN_PIPE || error==ERROR_NO_DATA) return true;
    throw std::runtime_error("stdin pipe detection failed");
}
unsigned parse_uint(const wchar_t* v) {
    if (!v || !*v) throw std::runtime_error("missing number");
    unsigned long long n=0;
    for (const wchar_t* s=v;*s;++s) {
        if (*s<L'0' || *s>L'9') throw std::runtime_error("invalid number");
        n=n*10+unsigned(*s-L'0');
        if(n>UINT32_MAX) throw std::runtime_error("number overflows uint32");
    }
    return static_cast<unsigned>(n);
}
}

int wmain(int argc,wchar_t** argv) {
    // No COM/audio access until a complete, explicit authorization and target PID.
    if (argc!=8 || std::wstring(argv[1])!=L"--confirm-audio" ||
        std::wstring(argv[2])!=L"--pid" || std::wstring(argv[4])!=L"--rate" ||
        std::wstring(argv[6])!=L"--out") {
        std::cerr<<"Manual use only: capture_engine --confirm-audio --pid PID --rate 48000 --out PATH.wav\n";
        return 2;
    }
    try {
        unsigned pid=parse_uint(argv[3]);
        unsigned rate=parse_uint(argv[5]);
        if (!pid || pid==GetCurrentProcessId() || (rate!=44100 && rate!=48000 && rate!=96000))
            throw std::runtime_error("invalid target pid or rate");
        const std::filesystem::path output(argv[7]);
        if (output.extension()!=L".wav" || std::filesystem::exists(output) || !std::filesystem::is_directory(output.parent_path()))
            throw std::runtime_error("output must be a fresh WAV in an existing directory");
        // Confirm the target is a running process before enabling process-tree capture.
        HANDLE process=OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION|SYNCHRONIZE,FALSE,pid);
        if (!process) throw std::runtime_error("engine process PID not available");
        const bool alive=WaitForSingleObject(process,0)==WAIT_TIMEOUT;
        CloseHandle(process);
        if (!alive) throw std::runtime_error("engine process already exited");
        Apartment apartment;
        Capture stream;
        stream.client=capture_client(pid);
        WAVEFORMATEX fmt{WAVE_FORMAT_IEEE_FLOAT,2,rate,rate*8,8,32,0};
        const DWORD flags=AUDCLNT_STREAMFLAGS_LOOPBACK|AUDCLNT_STREAMFLAGS_EVENTCALLBACK|
                          AUDCLNT_STREAMFLAGS_AUTOCONVERTPCM|AUDCLNT_STREAMFLAGS_SRC_DEFAULT_QUALITY;
        check(stream.client->Initialize(AUDCLNT_SHAREMODE_SHARED,flags,200000,0,&fmt,nullptr),"Capture Initialize");
        HANDLE wake=CreateEventW(nullptr,FALSE,FALSE,nullptr);
        if (!wake) throw std::runtime_error("capture wake event unavailable");
        check(stream.client->SetEventHandle(wake),"SetEventHandle");
        ComPtr<IAudioCaptureClient> reader;
        check(stream.client->GetService(IID_PPV_ARGS(&reader)),"GetService");
        std::ofstream out(output,std::ios::binary|std::ios::trunc);
        if (!out) throw std::runtime_error("cannot create capture file");
        header(out,rate,0);
        check(stream.client->Start(),"Capture Start");
        stream.started=true;
        uint64_t size=0;
        const uint64_t limit=3500000000ULL;
        const std::vector<float> zeros(4096,0.f);
        const auto began=std::chrono::steady_clock::now();
        HANDLE input=GetStdHandle(STD_INPUT_HANDLE);
        while (!stop_requested(input) &&
               std::chrono::duration<double>(std::chrono::steady_clock::now()-began).count()<3700) {
            DWORD w=WaitForSingleObject(wake,10);
            if (w!=WAIT_TIMEOUT && w!=WAIT_OBJECT_0) throw std::runtime_error("capture wait failed");
            UINT32 frames=0;
            check(reader->GetNextPacketSize(&frames),"GetNextPacketSize");
            while (frames>0) {
                BYTE* data=nullptr; UINT32 count=0; DWORD packet_flags=0;
                UINT64 device_position=0,qpc=0;
                check(reader->GetBuffer(&data,&count,&packet_flags,&device_position,&qpc),"GetBuffer");
                if (size+uint64_t(count)*8>limit) {
                    reader->ReleaseBuffer(count);
                    throw std::runtime_error("capture file size exceeds 3.5 GB");
                }
                if (count>0) {
                    if (packet_flags&AUDCLNT_BUFFERFLAGS_SILENT) {
                        for (UINT32 offset=0;offset<count;) {
                            UINT32 n=std::min<UINT32>(count-offset,2048);
                            out.write(reinterpret_cast<const char*>(zeros.data()),std::streamsize(n*8));
                            offset+=n;
                        }
                    } else {
                        if (!data) {reader->ReleaseBuffer(count);throw std::runtime_error("null capture buffer");}
                        out.write(reinterpret_cast<const char*>(data),std::streamsize(count*8));
                    }
                    size+=uint64_t(count)*8;
                }
                check(reader->ReleaseBuffer(count),"ReleaseBuffer");
                if (!out) throw std::runtime_error("capture write failure");
                check(reader->GetNextPacketSize(&frames),"GetNextPacketSize");
            }
        }
        check(stream.client->Stop(),"Capture Stop");
        stream.started=false;
        CloseHandle(wake);
        if (size<8) throw std::runtime_error("empty capture");
        header(out,rate,static_cast<uint32_t>(size));
        out.close();
        if (!out) throw std::runtime_error("WAV finalization failed");
        return 0;
    } catch(const std::exception& e) {
        std::cerr<<"capture_engine: "<<e.what()<<"\n";
        return 1;
    }
}
