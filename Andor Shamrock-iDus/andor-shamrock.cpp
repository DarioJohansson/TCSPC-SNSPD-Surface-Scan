// main.cpp
#include <windows.h>
#include "andor-shamrock.h"
#include <stdio.h>
#include <stdlib.h>

// Static handle to the loaded DLL
static HMODULE lib = NULL;

// Global function pointers
Initialize_t Initialize = NULL;
GetCameraHandle_t GetCameraHandle = NULL;
GetAvailableCameras_t GetAvailableCameras = NULL;
SetCurrentCamera_t SetCurrentCamera = NULL;
GetHeadModel_t GetHeadModel = NULL;

void LoadAndorLibrary(const char* path) {
    if (lib != NULL) {
        // Already loaded
        return;
    }

    lib = LoadLibraryA(path);
    if (!lib) {
        fprintf(stderr, "Failed to load DLL: %s\n", path);
        exit(1);
    }

    // Load each function from the DLL
    Initialize = (Initialize_t)GetProcAddress(lib, "Initialize");
    GetCameraHandle = (GetCameraHandle_t)GetProcAddress(lib, "GetCameraHandle");
    GetAvailableCameras = (GetAvailableCameras_t)GetProcAddress(lib, "GetAvailableCameras");
    SetCurrentCamera = (SetCurrentCamera_t)GetProcAddress(lib, "SetCurrentCamera");
    GetHeadModel = (GetHeadModel_t)GetProcAddress(lib, "GetHeadModel");

    // Check for any NULL function pointers
    if (!Initialize || !GetCameraHandle || !GetAvailableCameras || !SetCurrentCamera || !GetHeadModel) {
        fprintf(stderr, "One or more functions failed to resolve.\n");
        exit(1);
    }
}
