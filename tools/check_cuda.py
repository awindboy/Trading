#!/usr/bin/env python3
import json,platform,sys
try:
 import torch
except Exception as e:
 print('CUDA CHECK FAIL: PyTorch import failed:',repr(e));sys.exit(2)
out={'python':platform.python_version(),'torch':torch.__version__,'cuda_available':torch.cuda.is_available(),'torch_cuda_build':torch.version.cuda,'device_count':torch.cuda.device_count()}
if torch.cuda.is_available():
 out['device_name']=torch.cuda.get_device_name(0);out['capability']=torch.cuda.get_device_capability(0);out['vram_gib']=round(torch.cuda.get_device_properties(0).total_memory/(1024**3),2)
print(json.dumps(out,indent=2))
if not torch.cuda.is_available():
 print('OFFICIAL V4 GPU RUN BLOCKED: install a CUDA-enabled PyTorch build using the current command from https://pytorch.org/get-started/locally/');sys.exit(3)
