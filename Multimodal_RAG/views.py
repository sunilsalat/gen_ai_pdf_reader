from django.shortcuts import render, redirect
from .forms import DocumentForm
from .models import Document, Document_Images
from django.http import JsonResponse
from unstructured.partition.pdf import partition_pdf
from .utils.s3Helper import upload_img_to_s3, upload_batch_images_to_s3, read_batch_images_from_s3_keys, get_path_from_folder
from .utils.extractImages import extract_images_using_partition_pdf, process_pdf_and_create_faiss_index
from .utils.chains import run_qa_chian
from django.conf import settings


def upload_pdf(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save()

            # extracting and storing images locally
            path = f"./media/{document.pdf_file}"
            raw_pdf_elements = extract_images_using_partition_pdf(path)

            # uploading images to s3
            images_path = "./media/images"
            upload_batch_images_to_s3(images_path)
            s3_keys = get_path_from_folder(images_path)

            # storing s3_key in Document_Images realted to Dcoument
            for i in s3_keys:
                Document_Images.objects.create(document=document, s3_key=i)
            # reading presigned url from s3 AND creating faiss index
            img_urls = read_batch_images_from_s3_keys(s3_keys)
            print("s3_keys", s3_keys)
            print("img_urls", img_urls)
            process_pdf_and_create_faiss_index(raw_pdf_elements, img_urls)

            return redirect('success/')
    else:
        form = DocumentForm()
    return render(request, 'upload.html', {'form': form})

def upload_success(request):
    return render(request, 'upload_success.html')


def get_answer(request):
    question = request.GET.get('question')

    relevant_docs = settings.DB.similarity_search(question)
    context = ""
    relevant_images = []

    for d in relevant_docs:
        if d.metadata['type'] == 'text':
            context += '[text]' + d.metadata['original_content']
        elif d.metadata['type'] == 'table':
            context += '[table]' + d.metadata['original_content']
        elif d.metadata['type'] == 'image':
            context += '[image]' + d.page_content
            relevant_images.append(d.metadata['original_content'])

    result = run_qa_chian(context, question)
    return JsonResponse({"relevant_images": relevant_images[0], "result": result})

def get_signed_url(request):
    key = request.GET.get('key')
    print(key)
    urls = read_batch_images_from_s3_keys([key])
    return JsonResponse({"singed_url" : urls})
