import argparse
import matplotlib.pyplot as plt
import cv2
import numpy as np
from resnet import Bottleneck as ResBlock
from sharpnet_model import *
from PIL import Image
from data_transforms import *
import os, sys
from scipy.misc import imsave
from imageio import imread

parser = argparse.ArgumentParser(description="Test a model on an image")
parser.add_argument('--image', '-i', dest='image_path', help="The input image", default=None)
parser.add_argument('--model', '-m', dest='model_path', help="checkpoint.pth to load as model")
parser.add_argument('--outpath', dest='outpath', default=None, help="Output directory where predictions will be saved")
parser.add_argument('--scale', dest='rescale_factor', default=1.0, type=float, help='Rescale factor (multiplicative)')
parser.add_argument('--cuda', dest='cuda_device', default='', help="To activate inference on GPU, set to GPU_ID")
parser.add_argument('--nocuda', action='store_true', help='Activate to disable GPU usage')
parser.add_argument('--normals', action='store_true', help='Activate to predict normals')
parser.add_argument('--depth', action='store_true', help='Activate to predict depth')
parser.add_argument('--boundary', action='store_true', help='Activate to predict occluding contours')
parser.add_argument('--display', action='store_true', help='Activate to display predictions')
parser.add_argument('--bias', action='store_true')

args = parser.parse_args()

if not args.nocuda:
    os.environ['CUDA_VISIBLE_DEVICES'] = str(args.cuda_device)
    device = torch.device("cuda" if args.cuda_device != '' else "cpu")
    # print("Running on " + torch.cuda.get_device_name(device))
else:
    device = torch.device('cpu')
    print("Running on CPU")

if args.bias:
    bias = True
else:
    bias = False

model = SharpNet(ResBlock, [3, 4, 6, 3], [2, 2, 2, 2, 2],
                 use_normals=True if args.normals else False,
                 use_depth=True if args.depth else False,
                 use_mask=False,
                 use_boundary=True if args.boundary else False,
                 bias_decoder=bias)

torch.set_grad_enabled(False)

model_dict = model.state_dict()

# Load model
trained_model_path = args.model_path
trained_model_dict = torch.load(trained_model_path, map_location=lambda storage, loc: storage)

# load image resnet encoder and mask_encoder and normals_decoder (not depth_decoder or normal resnet)
model_weights = {k: v for k, v in trained_model_dict.items() if k in model_dict}

model.load_state_dict(model_weights)
model.eval()
model.to(device)

t = []
normalize = Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
t.extend([ToTensor(), normalize])
transf = Compose(t)

image_path = args.image_path
model_path = args.model_path
def round_down(num, divisor):
    return num - (num % divisor)

scale = args.rescale_factor

mean_RGB = np.array([0.485, 0.456, 0.406])
mean_BGR = np.array([mean_RGB[2], mean_RGB[1], mean_RGB[0]])

image_np = imread(image_path)
image_pil = Image.open(image_path)
w, h = image_pil.size

h_new = round_down(int(h * scale), 16)
w_new = round_down(int(w * scale), 16)

if len(image_np.shape) == 2 or image_np.shape[-1] == 1:
    print("Input image has only 1 channel, please use an RGB or RGBA image")
    sys.exit(0)

if len(image_np.shape) == 4 or image_np.shape[-1] == 4:
    # RGBA image to be converted to RGB
    image_pil = image_pil.convert('RGBA')
    image = Image.new("RGB", (image_np.shape[1], image_np.shape[0]), (255, 255, 255))
    image.paste(image_pil.copy(), mask=image_pil.split()[3])
else:
    image = image_pil

image = image.resize((w_new, h_new), Image.ANTIALIAS)

image_original = image
normalize = Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
t = []
t.extend([ToTensor(), normalize])
transf = Compose(t)

data = [image, None]
image = transf(*data)

image = torch.autograd.Variable(image).unsqueeze(0)
image = image.to(device)

if args.boundary:
    if args.depth and args.normals:
        depth_pred, normals_pred, boundary_pred = model(image)
        tmp = normals_pred.data.cpu()
    elif args.depth and not args.normals:
        depth_pred, boundary_pred = model(image)
        tmp = depth_pred.data.cpu()
    elif args.normals and not args.depth:
        normals_pred, boundary_pred = model(image)
        tmp = normals_pred.data.cpu()
else:
    if args.depth:
        depth_pred = model(image)
        tmp = depth_pred.data.cpu()
    if args.depth and args.normals:
        depth_pred, normals_pred = model(image)
        tmp = normals_pred.data.cpu()
    if args.normals and not args.depth:
        normals_pred = model(image)
        tmp = normals_pred.data.cpu()

shp = tmp.shape[2:]

mask_pred = np.ones(shape=shp)
mask_display = mask_pred

if args.normals:
    normals_pred = normals_pred.data.cpu().numpy()[0, ...]
    normals_pred = normals_pred.swapaxes(0, 1).swapaxes(1, 2)
    normals_pred[..., 0] = 0.5 * (normals_pred[..., 0] + 1)
    normals_pred[..., 1] = 0.5 * (normals_pred[..., 1] + 1)
    normals_pred[..., 2] = -0.5 * np.clip(normals_pred[..., 2], -1, 0) + 0.5

    normals_pred[..., 0] = normals_pred[..., 0] * 255
    normals_pred[..., 1] = normals_pred[..., 1] * 255
    normals_pred[..., 2] = normals_pred[..., 2] * 255
    if args.display:
        plt.subplot(2, 2, 2)
        plt.imshow(normals_pred.astype('uint8'))
    if args.outpath is not None:
        imsave(os.path.join(args.outpath, os.path.basename(image_path).rsplit('.')[0] + '_normals.png'),
               normals_pred.astype('uint8'))

if args.depth:
    depth_pred = depth_pred.data.cpu().numpy()[0, 0, ...] * 65535 / 1000
    depth_pred = (1/scale) * cv2.resize(depth_pred, dsize=(image_original.size[0], image_original.size[1]),
                                    interpolation=cv2.INTER_LINEAR)
    if args.display:
        plt.subplot(2, 2, 4)
        plt.imshow(depth_pred)
        plt.set_cmap('jet')
    if args.outpath is not None:
        depth_pred = (depth_pred*10000).astype(np.uint16)
        cv2.imwrite(os.path.join(args.outpath, os.path.basename(image_path).rsplit('.')[0] + '_depth.png'),
                    depth_pred.astype(np.uint16))

if args.boundary:
    boundary_pred = boundary_pred.data.cpu().numpy()[0, 0, ...]
    boundary_pred = cv2.resize(boundary_pred, dsize=(image_original.size[0], image_original.size[1]),
                               interpolation=cv2.INTER_LINEAR)
    boundary_pred = np.clip(boundary_pred, 0, 10)

    if args.display:
        plt.subplot(2, 2, 3)
        plt.imshow(boundary_pred)
        plt.set_cmap('gray')
    if args.outpath is not None:
        imsave(os.path.join(args.outpath, os.path.basename(image_path).rsplit('.')[0] + '_boundary.png'),
               (boundary_pred*255).astype('uint8'))

if args.display:
    plt.subplot(2, 2, 1)
    plt.imshow(image_original)  # .swapaxes(0,1).swapaxes(1,2))
    plt.show()
