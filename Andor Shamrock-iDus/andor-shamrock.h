#ifndef ANDOR_SHAMROCK_H
#define ANDOR_SHAMROCK_H

#ifdef __cplusplus
extern "C" {
#endif

// Typedefs for the DLL-exported functions
typedef unsigned int (__stdcall *Initialize_t)(char*);
typedef unsigned int (__stdcall *GetCameraHandle_t)(long, long*);
typedef unsigned int (__stdcall *GetAvailableCameras_t)(long*);
typedef unsigned int (__stdcall *SetCurrentCamera_t)(long);
typedef unsigned int (__stdcall *GetHeadModel_t)(char*);

// Initializes the DLL (call this once before using the functions)
void LoadAndorLibrary(const char* path = "lib/atmcd64d.dll");

#ifdef __cplusplus
}
#endif

#endif // ANDOR_SHAMROCK_H