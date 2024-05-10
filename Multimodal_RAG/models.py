from django.db import models

# Create your models here.

class Document(models.Model):
    description = models.CharField(max_length=255, blank=True)
    pdf_file = models.FileField(upload_to='pdfs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.description


class Document_Images(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    s3_key = models.CharField(max_length=255)

    def __str__(self):
        return f"Image for {self.document.description}"
