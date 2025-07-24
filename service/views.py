from django.http import HttpResponse

def index(request):
    return HttpResponse("Service 앱입니다.")