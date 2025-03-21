# SharpNet
*Fast and Accurate Recovery of Occluding Contours in Monocular Depth Estimation*, 
by Michaël Ramamonjisoa and Vincent Lepetit.

Link to the paper: [arXiv](https://arxiv.org/abs/1905.08598)

<p align="center">
  <img src="architecture.png" width="800"/>
</p>

### Installation

Make sure you have installed the following requirements:

- Python3
- [Pytorch](https://pytorch.org/get-started/locally/)
- OpenCV
- numpy, scipy, Pillow, matplotlib

Clone the repository and download the [trained weights](https://drive.google.com/open?id=1UTruzxPxQdoxF44X7D27f8rISFU0bKMK):

```
git clone https://github.com/MichaelRamamonjisoa/SharpNet.git
cd SharpNet
mkdir models && cd models
```

Put the trained weights in the models/ directory.

## Demo

Try the [demo.py](https://github.com/MichaelRamamonjisoa/SharpNet/blob/master/demo.py) 
script to test our network on your image :

```
python3 demo.py --image $YOURIMAGEPATH \
--cuda $CUDA_DEVICE_ID\
--model models/final_checkpoint_NYU.pth \
--normals \
--depth \
--boundary \
--bias \
--scale $SCALEFACTOR 
```

The network was trained using 640x480 images, therefore better results might be 
observed after rescaling the image with $SCALEFACTOR different than 1. 

Here is what you can get on your test image:
![alt_text](https://github.com/MichaelRamamonjisoa/MichaelRamamonjisoa.github.io/blob/master/images/SharpNet_thumbnail.gif)

## Training

The PBRS dataset is currently offline due to instructions of SUNCG author (see 
[this](https://github.com/yindaz/pbrs/issues/11) and [this](https://github.com/shurans/SUNCGtoolbox/issues/32)). 
Therefore reproduction of our training procedure cannot be done properly. However we will provide code for loss
computation, finetuning on the NYUv2 Depth dataset as well as our pretrained weights on the PBRS dataset only.

## Evaluation

TODO

## Citation

If you find SharpNet useful in your research, please consider citing:
```
@article{ramamonjisoa2019sharpnet,
    Title = {SharpNet: Fast and Accurate Recovery of Occluding Contours in Monocular Depth Estimation},
    Author = {Michael Ramamonjisoa and Vincent Lepetit},
    Journal = {arXiv preprint arXiv:1905.08598},
    Year = {2019}
}
```
