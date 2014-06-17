from django.shortcuts import redirect 

## Goodbye FAQ
# <3 Dyl

def redirect_to_fle_faq(request, topic_slug, slug):
    return redirect('https://learningequality.org/ka-lite/faq#faq-question-%s' % slug, permanent=True)
