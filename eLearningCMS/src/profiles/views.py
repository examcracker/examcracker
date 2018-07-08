from __future__ import unicode_literals
from django.views import generic
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from . import forms
from . import models


class ShowProfile(LoginRequiredMixin, generic.TemplateView):
    template_name = "profiles/show_profile.html"
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        slug = self.kwargs.get('slug')
        if slug:
            profile = get_object_or_404(models.Profile, slug=slug)
            user = profile.user
        else:
            user = self.request.user

        if user == self.request.user:
            kwargs["editable"] = True
        kwargs["show_user"] = user
        return super().get(request, *args, **kwargs)


class EditProfile(LoginRequiredMixin, generic.TemplateView):
    template_name = "profiles/edit_profile.html"
    http_method_names = ['get', 'post']

    def get(self, request, *args, **kwargs):
        user = self.request.user
        if "user_form" not in kwargs:
            kwargs["user_form"] = forms.UserForm(instance=user)
        if "profile_form" not in kwargs:
            kwargs["profile_form"] = forms.ProfileForm(instance=user.profile)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        user_form = forms.UserForm(request.POST, instance=user)
        profile_form = forms.ProfileForm(request.POST,
                                         request.FILES,
                                         instance=user.profile)
        if not (user_form.is_valid() and profile_form.is_valid()):
            messages.error(request, "There was a problem with the form. "
                           "Please check the details.")
            user_form = forms.UserForm(instance=user)
            profile_form = forms.ProfileForm(instance=user.profile)
            return super().get(request,
                               user_form=user_form,
                               profile_form=profile_form)
        # Both forms are fine. Time to save!
        user_form.save()
        profile = profile_form.save(commit=False)
        profile.user = user
        profile.save()
        messages.success(request, "Profile details saved!")
        return redirect("profiles:show_self")

class MyProfile(LoginRequiredMixin, generic.TemplateView):
    http_method_names = ['get', 'post']

    def get(self, request, *args, **kwargs):
        profileObj = models.Profile.objects.filter(user_id=request.user.id)[0]
        kwargs["userDetails"] = profileObj
        kwargs["authUserDetails"] = request.user
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        userObj = request.user
        profileObj = models.Profile.objects.filter(user_id=request.user.id)[0]
        picture = self.request.FILES.get("profile_pic")
        if picture is not None:
            profileObj.picture = picture

        profileObj.bio = self.request.POST.get("bio")
        profileObj.address = self.request.POST.get("address")
        profileObj.city = self.request.POST.get("city")
        profileObj.country = self.request.POST.get("country")
        profileObj.phone = self.request.POST.get("mobile")
        userObj.name = self.request.POST.get("name")

        userObj.save()
        profileObj.save()
