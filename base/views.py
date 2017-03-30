from django.shortcuts import render
from django.views.generic import View
import oeplatform.securitysettings as sec
from django.core.mail import send_mail
from base.forms import ContactForm

# Create your views here.

class Welcome(View):
   
    def get(self, request):
        return render(request,'base/index.html',{}) 


def redir(request, target):
    return render(request, 'base/{target}.html'.format(target=target),{})


class ContactView(View):
    def post(self, request):
        form = ContactForm(data=request.POST)
        if form.is_valid():
            receps = sec.CONTACT_ADDRESSES[request.POST['contact']]
            send_mail(
                request.POST.get('contact_topic'),
                request.POST.get(
                    'contact_name') + " wrote: \n" + request.POST.get('content'),
            request.POST.get('contact_email'),
                receps,
                fail_silently=False,
            )
            return render(request, 'base/contact.html', {'form': ContactForm(),
                                                         'success':True})
        else:
            return render(request, 'base/contact.html', {'form': form,
                                                         'success': False})
    def get(self, request):
        print(ContactForm().as_table())
        return render(request, 'base/contact.html',
                      {'form': ContactForm(), 'success': False})


def handler500(request):
    response = render(request,'base/500.html', {})
    response.status_code = 500
    return response