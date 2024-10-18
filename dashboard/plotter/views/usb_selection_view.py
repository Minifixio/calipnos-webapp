from django.shortcuts import render

def usb_selection(request):
    return render(request, 'usb_selection.html', {})