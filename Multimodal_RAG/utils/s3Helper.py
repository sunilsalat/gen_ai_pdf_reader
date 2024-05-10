
from django.conf import settings
import boto3
import os
from .common  import remove_leading_dots

s3 = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY, region_name=settings.AWS_REGION)


def upload_img_to_s3(image_path):
    with open(image_path, "rb") as f:
      s3.upload_fileobj(f, settings.S3_BUCKET_NAME, remove_leading_dots(image_path))
    return image_path


def upload_batch_images_to_s3(output_path):
    for i in os.listdir(output_path):
        image_path = os.path.join(output_path, i)
        upload_img_to_s3(image_path)
    return 'Images Uploaded'


def read_img_from_s3(image_key):
    image_url = s3.generate_presigned_url(
        ClientMethod='get_object',
        Params={'Bucket': settings.S3_BUCKET_NAME, 'Key': image_key},
        ExpiresIn=3600  # URL expiration time in seconds (optional)
    )
    return image_url



def read_batch_images_to_s3(output_path):
    img_urls = []
    for i in os.listdir(output_path):
        image_path = os.path.join(output_path, i)
        read_img_from_s3(image_path)
    return img_urls

def read_batch_images_from_s3_keys(s3_keys):
    img_urls = []
    for i in s3_keys:
       url= read_img_from_s3(i)
       img_urls.append(url)
    return img_urls

def get_path_from_folder(dir_path):
    paths = []
    for i in os.listdir(dir_path):
        image_path = os.path.join(remove_leading_dots(dir_path), i)
        paths.append(image_path)
    return paths


__all__ = ['upload_img_to_s3', 'read_img_from_s3', 'upload_batch_images_to_s3', 'read_batch_images_to_s3', 'read_batch_images_from_s3_keys', "get_path_from_folder" ]
