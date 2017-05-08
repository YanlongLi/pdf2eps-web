
import sys
import os
from os.path import basename
import subprocess
import zipfile

from django.conf import settings
from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from wsgiref.util import FileWrapper
from django.utils.encoding import smart_str
import mimetypes

# https://simpleisbetterthancomplex.com/tutorial/2016/08/01/how-to-upload-files-with-django.html

def index(request):
    context = {}
    if request.method == 'POST':
        f = request.FILES['file']
        fs = FileSystemStorage()
        filename = f.name
        filepath = os.path.join(settings.MEDIA_ROOT, filename)
        if os.path.isfile(filepath):
            os.remove(filepath)
        fs.save(f.name, f)
        cropfile = os.path.join(settings.MEDIA_ROOT, os.path.splitext(filename)[0] + "-crop.pdf")
        epsfile = os.path.join(settings.MEDIA_ROOT, os.path.splitext(filename)[0] + "-crop.eps")
        zfile = os.path.join(settings.MEDIA_ROOT, os.path.splitext(filename)[0] + ".zip")
        subprocess.call(['pdfcrop', filepath, cropfile])
        subprocess.call(['pdftops', '-eps', cropfile, epsfile])
        zf = zipfile.ZipFile(zfile, mode='w')
        try:
            zf.write(filepath, basename(filepath))
            zf.write(cropfile, basename(cropfile))
            zf.write(epsfile, basename(epsfile))
        finally:
            zf.close()
        zipurl = fs.url(zfile)
        print >>sys.stderr, filepath
        print >>sys.stderr, filename
        print >>sys.stderr, zipurl
        # file_path = settings.MEDIA_ROOT +'/'+ file_name
        file_path = zipurl
        file_wrapper = FileWrapper(file(file_path,'rb'))
        file_mimetype = mimetypes.guess_type(file_path)
        response = HttpResponse(file_wrapper, content_type=file_mimetype )
        response['X-Sendfile'] = file_path
        response['Content-Length'] = os.stat(file_path).st_size
        response['Content-Disposition'] = 'attachment; filename=%s' % basename(file_path)
        return response
    else:
        return render(request, 'index.html', context)

