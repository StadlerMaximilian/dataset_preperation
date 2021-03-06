import json
import sys
import os
import argparse

from argparse import Namespace

from get_dataset_statistics import statistics_routine
from get_dataset_specs import specs_routine

"""
Utilites to remove categories that should be ignored during testing
"""


def parse_args():
    parser = argparse.ArgumentParser(
        description='Create subsets of dataset containing mainly large or mainly small images'
    )
    parser.add_argument(
        '--json',
        dest='json_file',
        type=str,
        help="Path to your json annotations to be modified.",
        default=""
    )

    parser.add_argument(
        '--mean',
        dest='mean',
        type=int,
        help='Mean Value of annotation sizes used for separation (side lengthof square!)',
        default="",
        required=True
    )

    parser.add_argument(
        '--frac',
        dest='fraction',
        type=float,
        help="Minimal Fraction of small/large objects in one image.",
        required=True
    )

    parser.add_argument(
        '--vis',
        help='Flag for printing specs and statistics of new datasets for feedback',
        action='store_true'
    )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    return parser.parse_args()


def create_coco_dataset_dict(new_images, new_annotations, categories, licenses, info):
    dataset_dict = {"info": info,
                    "images": new_images,
                    "annotations": new_annotations,
                    "type": "instances",
                    "licenses": licenses,
                    "categories": categories
                    }

    return dataset_dict


def main():
    args = parse_args()

    if not os.path.exists(args.json_file):
        raise ValueError("FILE {} does not exist!!!".format(args.json_file))
    json_file = json.loads(open(args.json_file).read())
    json_file_name = args.json_file.split('.')[0]

    categories = json_file['categories']
    info = json_file['info']
    images = json_file['images']
    annotations = json_file['annotations']
    licenses = json_file['licenses']

    anno_per_img_dict = {}
    img_id_dict = {}

    for img in images:
        img_annos = []
        id = img['id']
        for anno in annotations:
            if anno['image_id'] == id:
                img_annos.append(anno)
        anno_per_img_dict[id] = img_annos
        img_id_dict[id] = img

    new_images_small = []
    new_images_large = []
    new_annotations_small = []
    new_annotations_large = []

    for id, anno_list in anno_per_img_dict.items():
        annos_small = []
        annos_large = []
        size_annos = len(anno_list)
        for anno in anno_list:
            if anno['area'] <= args.mean**2:
                annos_small.append(anno)
            else:  # area > thresh
                annos_large.append(anno)
        if len(annos_small) >= max(round(size_annos * args.fraction), 1):
            # if more small annotations than needed
            # add small annotations and large annotations to new_images_small
            new_annotations_small.extend(anno_list)
            new_images_small.append(img_id_dict[id])
        if len(annos_large) >= max(round(size_annos * args.fraction), 1):
            new_annotations_large.extend(anno_list)
            new_images_large.append(img_id_dict[id])

    new_dataset_dict_small = create_coco_dataset_dict(new_images_small, new_annotations_small,
                                                      categories, licenses, info)

    new_dataset_dict_large = create_coco_dataset_dict(new_images_large, new_annotations_large,
                                                      categories, licenses, info)

    with open(json_file_name + '_small.json', 'w') as fp:
        json.dump(new_dataset_dict_small, fp)
    print("wrote file {}".format(json_file_name + '_small.json'))
    with open(json_file_name + '_large.json', 'w') as fp:
        json.dump(new_dataset_dict_large, fp)
    print("wrote file {}".format(json_file_name + '_large.json'))

    if args.vis:
        parser_specs = argparse.ArgumentParser()
        parser_specs.add_argument('--ann_dir', dest='ann_dir')
        parser_specs.add_argument('--type', dest='data_type', default="default")
        parser_specs.add_argument('--json', dest='json')

        parser_stats = argparse.ArgumentParser()
        parser_stats.add_argument('--json', dest='json_files', action='append')

        args_specs_large = parser_specs.parse_args(['--json', '{}'.format(json_file_name + '_large.json')])
        args_specs_small = parser_specs.parse_args(['--json', '{}'.format(json_file_name + '_small.json')])

        args_statistics_large = parser_stats.parse_args(['--json', '{}'.format(json_file_name + '_large.json')])
        args_statistics_small = parser_stats.parse_args(['--json', '{}'.format(json_file_name + '_small.json')])

        print('\n---------------------------\n')
        print('Evaluating statistics of subset of large objcets')
        specs_routine(args_specs_large)
        statistics_routine(args_statistics_large)

        print('\n---------------------------\n')
        print('Evaluating statistics of subset of small objcets')
        specs_routine(args_specs_small)
        statistics_routine(args_statistics_small)


if __name__ == '__main__':
    main()

