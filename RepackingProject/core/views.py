from django.views import View
from django.shortcuts import render, redirect
from django.views.decorators.cache import cache_page


class HomeView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect("login")

        return redirect("repacking-records")


# @cache_page(60 * 60 * 12)
def not_found_view(request, exception=None):
    context = {}
    return render(request, '404.html', context=context)
