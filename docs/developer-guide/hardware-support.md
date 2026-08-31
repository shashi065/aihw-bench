# Advanced Hardware Support

AIHW-Bench uses four explicit capability states:

| State | Meaning |
| --- | --- |
| **Detected** | A host or runtime probe identified the hardware/software. |
| **Reportable** | Its metadata can be saved in a `HardwareProfile` and shown in reports. |
| **Runnable** | A built-in or installed plugin backend can execute a benchmark for that target. |
| **Accelerated** | The selected workload/runtime actually uses that hardware acceleration path. |

Detection and reporting do **not** imply runnable or accelerated execution.

## CPU and GPU capabilities

- **Intel / AMD CPUs:** detected and reportable through portable host probes. The CPU backend is runnable; acceleration depends on the selected model runtime.
- **Apple Silicon:** detected/reportable on Darwin ARM hosts. CPU execution is runnable; Metal/MPS acceleration requires a compatible installed runtime and is not provided by the generic CPU backend.
- **NVIDIA:** CUDA is reportable only when the CUDA runtime reports available devices. `cuda` targets are runnable only when that capability is present; acceleration depends on the workload runtime.
- **AMD:** ROCm is reportable only when the ROCm runtime reports available devices. `rocm`/`hip` targets are rejected unless ROCm is available.
- **Intel GPU:** Intel GPUs may be detected from Linux DRM data and are reportable. `intel-gpu`/`xpu` targets are accepted only if that normalized capability is present; oneAPI execution requires an appropriate installed backend/runtime.
- **Unknown GPU or missing runtime:** may be detected as hardware, but concrete CUDA/ROCm/Intel targets are not runnable and are rejected with a diagnostic.

## Embedded and specialized targets

- **Raspberry Pi, Jetson, Coral:** device metadata is detected/reportable best-effort. A compatible model/runtime/backend is required for runnable or accelerated workloads.
- **FPGA:** environment metadata creates a reportable placeholder only. The built-in placeholder deliberately cannot execute; install a board-specific plugin for runnable support.
- **RTL simulator:** provenance and requested observations are reportable. The RTL backend normalizes supplied observations but does not invoke vendor simulator binaries.

`HardwareProfile.capability_report()` is the normalized contract used for backend selection. It records availability, vendors, device count, and concrete runtime capabilities such as `cuda`, `rocm`, or `intel-gpu`.
