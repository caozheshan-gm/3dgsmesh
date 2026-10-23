import torch
print('torch', torch.__version__, 'CUDA runtime', torch.version.cuda, 'available', torch.cuda.is_available(), flush=True)
assert torch.cuda.is_available()
print('GPU', torch.cuda.get_device_name(0), flush=True)
x = torch.randn((512, 512), device='cuda', requires_grad=True)
loss = (x @ x).square().mean()
loss.backward()
print('GPU_GRAD_OK', float(loss.detach()), flush=True)
