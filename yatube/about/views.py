from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    template_name = 'about/author.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['just_title'] = 'Я простой человек'
        context['just_text'] = ('Веду обычный образ жизни. '
                                'Вот и все')
        return context


class AboutTechView(TemplateView):
    template_name = 'about/tech.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['just_title'] = 'Что Вам интеоресно?'
        context['just_text'] = ('Здесь ничего толком не будет. '
                                'Н И Ч Е Г О !!')
        return context
