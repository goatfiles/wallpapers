#!/usr/bin/env python3
from typing import List, Tuple

import os
import argparse
from tqdm import tqdm

import numpy as np
import cv2
from colorama import Fore, Back, Style


def load_image(filename: str, *, path: str) -> np.ndarray:
    return cv2.imread(os.path.join(path, filename))


def load_images(filenames: List[str], *, path: str) -> List[np.ndarray]:
    images = []
    for filename in tqdm(filenames, desc=f"Loading images in {path}"):
        image = load_image(filename, path=path)
        images.append(image)
    return images


def is_good_ratio(
    width: int,
    height: int,
    *,
    ratio: Tuple[int, int] = (16, 9),
) -> bool:
    return bool(width == int(height * ratio[0] / ratio[1]))


def is_resizable(
    width: int,
    height: int,
    *,
    margin: float,
    ratio: Tuple[int, int] = (16, 9),
):
    return abs(width / height - ratio[0] / ratio[1]) <= margin


def get_closest_shape(
    width: int,
    height: int,
    *,
    valid_shapes: np.ndarray,
    ratio: Tuple[int, int] = (16, 9),
) -> Tuple[int, int]:
    if is_good_ratio(width, height, ratio=ratio):
        return (height, width)

    bad_shape = np.array([height, width])
    index = np.sum(np.square(valid_shapes - bad_shape), axis=1).argmin()
    return valid_shapes[index]


def compute_all_valid_shapes(
    shapes: np.ndarray,
    *,
    ratio: Tuple[int, int] = (16, 9),
) -> np.ndarray:
    ratio = np.array(ratio)
    max_ratio = np.max(shapes / ratio).astype(int)
    ratio_range = np.arange(1, max_ratio + 1)
    valid_shapes = np.dot(ratio_range[:, None], ratio[None, :])
    return valid_shapes[:, ::-1]


def resize_image(
    *,
    filename: str,
    image: np.ndarray,
    valid_shapes: np.ndarray,
    path: str,
    ratio: Tuple[int, int],
) -> None:
    height, width = image.shape[:2]
    print(f"{Fore.YELLOW}[WARN.]{Style.RESET_ALL} {filename}: Resizing...", end="")
    closest_shape = get_closest_shape(
        width, height, valid_shapes=valid_shapes, ratio=ratio
    )
    resized_image = cv2.resize(image, closest_shape[::-1])
    cv2.imwrite(os.path.join(path, filename), resized_image)
    print("done!")


def get_biggest_shape_contained_in_image(
    shape: np.ndarray, *, valid_shapes: np.ndarray
) -> np.ndarray:
    for i, valid_shape in enumerate(valid_shapes):
        if np.any(shape < valid_shape):
            break
    return valid_shapes[i - 1]


def crop_image(
    *,
    filename: str,
    image: np.ndarray,
    valid_shapes: np.ndarray,
    path: str,
) -> None:
    print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {filename}: Manual...")

    old_shape = np.array(image.shape[:2])
    new_shape = get_biggest_shape_contained_in_image(
        old_shape, valid_shapes=valid_shapes
    )

    # compute the margin on each side.
    margin = old_shape - new_shape
    up_left_margin = margin // 2
    down_right_margin = margin - up_left_margin
    left_margin, up_margin = up_left_margin
    right_margin, down_margin = down_right_margin

    # remove the margins on each side.
    width, height = old_shape
    cropped_image = image[
        left_margin : width - right_margin, up_margin : height - down_margin
    ]
    cv2.imwrite(os.path.join(path, filename), cropped_image)


def show_image(image: np.ndarray, *, title: str = "Title") -> None:
    cv2.imshow(title, image)
    cv2.waitKey(0)


def main(*, path: str, ratio: Tuple[int, int], margin: float, verbose: bool) -> None:
    filenames = sorted(os.listdir(path))
    wallpapers = load_images(filenames, path=path)

    shapes = [wallpaper.shape[:2] for wallpaper in wallpapers]
    valid_shapes = compute_all_valid_shapes(shapes, ratio=ratio)

    for wallpaper, filename in zip(wallpapers, filenames):
        height, width = wallpaper.shape[:2]
        if is_good_ratio(width, height, ratio=ratio):
            if verbose:
                print(f"{Fore.GREEN}[OK...]{Style.RESET_ALL} {filename}: Skipping...")
        elif is_resizable(width, height, ratio=ratio, margin=margin):
            resize_image(
                filename=filename,
                image=wallpaper,
                valid_shapes=valid_shapes,
                path=path,
                ratio=ratio,
            )
        else:
            crop_image(
                filename=filename,
                image=wallpaper,
                valid_shapes=valid_shapes,
                path=path,
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-p",
        "--path",
        required=True,
        type=str,
        help="The path to the wallpapers.",
    )
    parser.add_argument(
        "-r",
        "--ratio",
        nargs=2,
        type=int,
        default=[16, 9],
        help="TODO.",
    )
    parser.add_argument(
        "-m",
        "--margin",
        type=float,
        default=0.17778,
        help="TODO.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="TODO.",
    )

    args = parser.parse_args()

    main(path=args.path, ratio=args.ratio, margin=args.margin, verbose=args.verbose)
