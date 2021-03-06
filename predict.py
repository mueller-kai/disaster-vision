# USAGE
# python predict.py
# import the necessary packages
import config
import matplotlib.pyplot as plt
import numpy as np
import torch
import cv2
import os
from PIL import Image


def prepare_plot(origImage, origMask, predMask):
    # initialize our figure
    figure, ax = plt.subplots(nrows=1, ncols=3, figsize=(10, 10))
    # plot the original image, its mask, and the predicted mask
    ax[0].imshow(origImage)
    ax[1].imshow(origMask)
    ax[2].imshow(predMask)
    # set the titles of the subplots
    ax[0].set_title("Image")
    ax[1].set_title("Original Mask")
    ax[2].set_title("Predicted Mask")
    # set the layout of the figure and display it
    # figure.tight_layout()
    # figure.show()
    plt.savefig("plot.png")
    plt.show


def make_predictions(model, imagePath, imagecounter):
    # set model to evaluation mode
    model.eval()

    threshhold = round(config.THRESHOLD * 100)
    # turn off gradient tracking
    with torch.no_grad():
        # load the image from disk, swap its color channels, cast it
        # to float data type, and scale its pixel values
        image = cv2.imread(imagePath)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = image.astype("float32") / 255.0

        # resize the image and make a copy of it for visualization
        # image = cv2.resize(image, (128, 128))
        orig = image.copy()
        # find the filename and generate the path to ground truth mask
        filename = imagePath.split(os.path.sep)[-1]

        # add "target" to groundtruth
        groundTruthfilename = (filename[:-4]) + "_target.png"
        groundTruthPath = os.path.join("test/" + "targets/" + groundTruthfilename)

        # save groundtruth to evaluate xview2_scoring.py
        gt_target = cv2.imread(groundTruthPath, 0)
        imagecounter = "{0:0>5}".format(imagecounter)
        cv2.imwrite(f"predictionT{threshhold}/gt-targets/test_localization_{imagecounter}_target.png", gt_target)
        cv2.imwrite(f"predictionT{threshhold}/gt-targets/test_damage_{imagecounter}_target.png", gt_target)

        # make the channel axis to be the leading one, add a batch
        # dimension, create a PyTorch tensor, and flash it to the
        # current device
        image = np.transpose(image, (2, 0, 1))
        image = np.expand_dims(image, 0)
        image = torch.from_numpy(image).to(config.DEVICE)

        # make the prediction, pass the results through the sigmoid
        # function, and convert the result to a NumPy array
        predMask = model(image).squeeze()
        predMask = torch.sigmoid(predMask)
        predMask = predMask.cpu().numpy()

        # filter out the weak predictions and convert them to integers
        print("predicted", predMask.max())
        predMask = predMask > config.THRESHOLD

        predMask = predMask.astype(np.uint8)

        # create a visible Prediction
        visible_prediction = predMask * 255
        visible_prediction = Image.fromarray(visible_prediction)
        visible_prediction.save(
            f"predictionT{threshhold}/visible-predictions/test_localization_{imagecounter}_prediction.png"
        )

        # save prediction mask
        predMaskimg = Image.fromarray(predMask)
        filename = filename[:-17]
        print(f"input image: {filename} ,", imagecounter)

        # save prediction Masks but save localisation as damage prediction as well
        predMaskimg.save(f"predictionT{threshhold}/predictions/test_localization_{imagecounter}_prediction.png")
        predMaskimg.save(f"predictionT{threshhold}/predictions/test_damage_{imagecounter}_prediction.png")

        # prepare a plot for visualization
        # prepare_plot(orig, gt_target, predMask)


if __name__ == "__main__":
    """
    This script will make predictions base on the configurations in config.py
    The predictions are saved in a folder called f"predictionsT{config.thershhold * 100}"
    The files will be saved and named in the way that scoring_xview2.py expects it
    The predictions and targets for damage are copies of the localization respectively,
    since for this challenge only localization is relevant

    """
    print("[INFO] loading up test image paths...")
    imagePaths = config.TEST_PATHS

    # load our model from disk and flash it to the current device
    print("[INFO] load up model", config.MODEL_PATH)
    print("threshhold:", config.THRESHOLD)
    unet = torch.load(config.MODEL_PATH).to(config.DEVICE)
    # iterate over the randomly selected test image paths
    imagecounter = 0
    for path in imagePaths:
        # make predictions and visualize the results
        make_predictions(unet, path, imagecounter)
        imagecounter += 1
