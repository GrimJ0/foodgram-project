import json
import uuid

from django.contrib import messages
from django.http import JsonResponse
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.edit import ModelFormMixin

from .models import Recipe
from .utils import add_ingredient, add_tag


class DataMixin(TemplateResponseMixin, ModelFormMixin):
    """
    Миксин для создания ингредиентов, тегов и добавления в рецепт
    """

    def user_form_valid(self, request, get_context_data, form):
        ingredients = add_ingredient(request)
        tags = add_tag(request)
        if not tags:
            messages.error(request, 'Нужно выбрать хотя бы один тег')
            return self.render_to_response(get_context_data(form=form))
        if not ingredients:
            messages.error(request, 'Вы забыли выбрать ингредиент')
            return self.render_to_response(get_context_data(form=form))
        recipe = form.save(commit=False)
        recipe.author = request.user
        recipe.tag = tags
        recipe.save()
        recipe.ingredient.clear()
        recipe.ingredient.add(*ingredients)
        return super().form_valid(form)


class AddMixin:

    @staticmethod
    def user_post(request, obj):
        data = {"success": False}
        recipe_id = json.loads(request.body).get('id')
        recipe = Recipe.objects.get(id=recipe_id)
        if request.user.is_authenticated:
            user = request.user
            exists = obj.objects.filter(user=user, recipe=recipe).exists()
            if not exists:
                _, succeed = obj.objects.get_or_create(user=user, recipe=recipe)
                data = {"success": succeed}
        else:
            if not request.session.get('purchase_id'):
                session_key = request.session['purchase_id'] = str(uuid.uuid4())
                exists = obj.objects.filter(session_key=session_key, recipe=recipe).exists()
                if not exists:
                    _, succeed = obj.objects.get_or_create(session_key=session_key, recipe=recipe)
                    data = {"success": succeed}
            else:
                session_key = request.session.get('purchase_id')
                exists = obj.objects.filter(session_key=session_key, recipe=recipe).exists()
                if not exists:
                    _, succeed = obj.objects.get_or_create(session_key=session_key, recipe=recipe)
                    data = {"success": succeed}
        return JsonResponse(data, safe=False)


class RemoveMixin:

    @staticmethod
    def user_delete(request, id, obj):
        data = {"success": False}
        recipe = Recipe.objects.get(id=id)
        if request.user.is_authenticated:
            user = request.user
            model = obj.objects.filter(user=user, recipe=recipe)
            if model.exists():
                succeed = model.delete()
                data = {"success": succeed}
        else:
            session_key = request.session.get('purchase_id')
            model = obj.objects.filter(session_key=session_key, recipe=recipe)
            if model.exists():
                succeed = model.delete()
                data = {"success": succeed}
        return JsonResponse(data, safe=False)
